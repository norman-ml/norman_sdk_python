from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

import jwt
from norman_core.clients.http_client import HttpClient
from norman_core.services.authenticate import Authenticate
from norman_objects.services.authenticate.login.account_id_password_login_request import AccountIDPasswordLoginRequest
from norman_objects.services.authenticate.login.api_key_login_request import ApiKeyLoginRequest
from norman_objects.services.authenticate.register.register_auth_factor_request import RegisterAuthFactorRequest
from norman_objects.services.authenticate.signup.signup_password_request import SignupPasswordRequest
from norman_objects.shared.security.sensitive import Sensitive
from norman_utils_external.singleton import Singleton


class AuthenticationManager(metaclass=Singleton):
    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key
        self._account_id = None
        self._access_token: Optional[Sensitive[str]] = None

    @property
    def access_token(self) -> Optional[Sensitive[str]]:
        return self._access_token

    @property
    def account_id(self) -> Optional[str]:
        return self._account_id

    @property
    def access_token_expired(self) -> bool:
        if self._access_token is None:
            return True
        try:
            decoded = jwt.decode(self._access_token.value(), options={"verify_signature": False})
            exp = decoded["exp"]
            now = datetime.now(timezone.utc).timestamp()
            return exp < now
        except Exception:
            return True

    async def login_internal(self):
        async with HttpClient() as http_client:
            if self._api_key is not None and self._api_key != "":
                request = ApiKeyLoginRequest(api_key=Sensitive(self._api_key))
                login_response = await Authenticate.login.login_with_key(http_client, request)
            else:
                login_response = await Authenticate.signup.signup_default(http_client)

            self._account_id = login_response.account.id
            self._access_token = login_response.access_token

    @staticmethod
    async def signup_with_password(username: str, password: str):
        async with HttpClient() as http_client:
            signup_request = SignupPasswordRequest(name=username, password=Sensitive(password))
            account = await Authenticate.signup.signup_with_password(http_client, signup_request)

            login_request = AccountIDPasswordLoginRequest(account_id=account.id, password=Sensitive(password))
            login_response = await Authenticate.login.login_password_account_id(http_client, login_request)
            first_access_token = login_response.access_token

            login_request = AccountIDPasswordLoginRequest(account_id=account.id, password=Sensitive(password))
            login_response = await Authenticate.login.login_password_account_id(http_client, login_request)
            second_access_token = login_response.access_token

            generate_api_key_request = RegisterAuthFactorRequest(account_id=account.id, second_token=second_access_token)
            api_key = await Authenticate.register.generate_api_key(http_client, first_access_token, generate_api_key_request)

            return {
                "account": account,
                "api_key": api_key,
                "message": "Signup successful. Your API key has been generated. Please copy and store it securely — it will not be shown again."
            }

    @asynccontextmanager
    async def get_http_client(self, login=True):
        http_client = HttpClient()
        if login and self.access_token_expired:
            await self.login_internal()
        yield http_client
        await http_client.close()
