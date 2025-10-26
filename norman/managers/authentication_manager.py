from datetime import datetime, timezone
from typing import Optional

import jwt
from norman_core.clients.http_client import HttpClient
from norman_core.services.authenticate import Authenticate
from norman_objects.services.authenticate.login.api_key_login_request import ApiKeyLoginRequest
from norman_objects.services.authenticate.signup.signup_key_request import SignupKeyRequest
from norman_objects.services.authenticate.signup.signup_key_response import SignupKeyResponse
from norman_objects.shared.security.sensitive import Sensitive
from norman_utils_external.singleton import Singleton


class AuthenticationManager(metaclass=Singleton):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._account_id = None
        self._access_token: Optional[Sensitive[str]] = None
        self._id_token: Optional[Sensitive[str]] = None

        self._authentication_service = Authenticate()
        self._http_client = HttpClient()

    @property
    def access_token(self) -> Sensitive[str]:
        if self._access_token is None:
            raise ValueError("Access token is not available — you may need to log in first.")
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

    async def login_internal(self) -> None:
        async with self._http_client:
            if self._api_key is not None and self._api_key != "":
                request = ApiKeyLoginRequest(api_key=Sensitive(self._api_key))
                login_response = await self._authentication_service.login.login_with_key(request)
            else:
                raise ValueError("API key is required. Please provide a valid API key.")

            self._account_id = login_response.account.id
            self._access_token = login_response.access_token
            self._id_token = login_response.id_token

    @staticmethod
    async def signup_and_generate_key(username: str) -> SignupKeyResponse:
        async with HttpClient():
            authentication_service = Authenticate()
            signup_request = SignupKeyRequest(name=username)
            response = await authentication_service.signup.signup_and_generate_key(signup_request)
            return response

    async def invalidate_access_token(self) -> None:
        if self.access_token_expired:
            await self.login_internal()
