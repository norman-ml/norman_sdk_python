from datetime import datetime, timezone
from typing import Optional

import jwt
from norman_core.clients.http_client import HttpClient
from norman_core.services.authenticate import Authenticate
from norman_objects.services.authenticate.login.account_id_password_login_request import AccountIDPasswordLoginRequest
from norman_objects.services.authenticate.login.api_key_login_request import ApiKeyLoginRequest
from norman_objects.services.authenticate.login.email_password_login_request import EmailPasswordLoginRequest
from norman_objects.services.authenticate.login.name_password_login_request import NamePasswordLoginRequest
from norman_objects.services.authenticate.signup.signup_key_request import SignupKeyRequest
from norman_objects.services.authenticate.signup.signup_key_response import SignupKeyResponse
from norman_objects.shared.authentication.account_authentication_methods import AccountAuthenticationMethods
from norman_objects.shared.security.sensitive import Sensitive
from norman_utils_external.singleton import Singleton


class AuthenticationManager(metaclass=Singleton):
    def __init__(self) -> None:
        self._authentication_service = Authenticate()
        self._http_client = HttpClient()

        self._api_key = None
        self._account_id = None
        self._access_token: Optional[Sensitive[str]] = None
        self._id_token: Optional[Sensitive[str]] = None

    @property
    def access_token(self) -> Sensitive[str]:
        if self._access_token is None:
            raise ValueError("Access token is not available — you may need to log in first")
        return self._access_token

    @property
    def account_id(self) -> Optional[str]:
        return self._account_id

    def set_api_key(self, api_key: str) -> None:
        self._api_key = api_key

    def access_token_expired(self) -> bool:
        if self._access_token is None:
            return True
        try:
            decoded = jwt.decode(self._access_token.value(), options={"verify_signature": False}) # we will add a jwks store to verify against in the near future.
            exp = decoded["exp"]
            now = datetime.now(timezone.utc).timestamp()
            return exp < now
        except Exception:
            return True

    @staticmethod
    async def signup_and_generate_key(username: str) -> SignupKeyResponse:
        async with HttpClient():
            authentication_service = Authenticate() # because signup_and_generate_key() is a static method
            signup_request = SignupKeyRequest(name=username)
            signup_response = await authentication_service.signup.signup_and_generate_key(signup_request)
            return signup_response

    # ==================== Get Authentication Factors ====================

    async def get_authentication_factors_by_id(self, account_id: str) -> AccountAuthenticationMethods:
        async with self._http_client:
            return await self._authentication_service.factors.get_authentication_factors_by_id(account_id)

    async def get_authentication_factors_by_name(self, account_name: str) -> AccountAuthenticationMethods:
        async with self._http_client:
            return await self._authentication_service.factors.get_authentication_factors_by_name(account_name)

    async def get_authentication_factors_by_email(self, email: str) -> AccountAuthenticationMethods:
        async with self._http_client:
            return await self._authentication_service.factors.get_authentication_factors_by_email(email)

    async def _login_with_api_key(self) -> None:
        async with self._http_client:
            if self._api_key is None or self._api_key == "":
                raise ValueError("API key is required. Please provide a valid API key")

            login_request = ApiKeyLoginRequest(api_key=Sensitive(self._api_key))
            login_response = await self._authentication_service.login.login_with_key(login_request)

            self._account_id = login_response.account.id
            self._access_token = login_response.access_token
            self._id_token = login_response.id_token

    def _set_login_response(self, login_response) -> None:
        """Helper to set tokens from login response"""
        self._account_id = login_response.account.id
        self._access_token = login_response.access_token
        self._id_token = login_response.id_token

        # ==================== Login Methods ====================

    async def login_with_api_key(self) -> None:
        """Login using the previously set API key"""
        async with self._http_client:
            await self._login_with_api_key()

    async def login_with_password_by_name(self, name: str, password: str) -> None:
        """Login with username and password"""
        async with self._http_client:
            login_request = NamePasswordLoginRequest(name=name, password=Sensitive(password))
            login_response = await self._authentication_service.login.login_password_name(login_request)
            self._set_login_response(login_response)

    async def login_with_password_by_email(self, email: str, password: str) -> None:
        """Login with email and password"""
        async with self._http_client:
            login_request = EmailPasswordLoginRequest(email=email, password=Sensitive(password))
            login_response = await self._authentication_service.login.login_password_email(login_request)
            self._set_login_response(login_response)

    async def login_with_password_by_account_id(self, account_id: str, password: str) -> None:
        """Login with account ID and password"""
        async with self._http_client:
            login_request = AccountIDPasswordLoginRequest(account_id=account_id, password=Sensitive(password))
            login_response = await self._authentication_service.login.login_password_account_id(login_request)
            self._set_login_response(login_response)

    async def login_default(self, account_id: str) -> None:
        """Login as guest (no authentication factors)"""
        async with self._http_client:
            login_response = await self._authentication_service.login.login_default(account_id)
            self._set_login_response(login_response)

    # ==================== Email OTP Methods ====================

    async def send_email_otp(self, email: str) -> None:
        """Request an OTP code to be sent to email"""
        async with self._http_client:
            await self._authentication_service.login.login_email_otp(email)

    async def verify_email_otp(self, email: str, code: str) -> None:
        """Verify OTP code and complete login"""
        async with self._http_client:
            login_response = await self._authentication_service.login.verify_email_otp(email, code)
            self._set_login_response(login_response)

    async def invalidate_access_token(self) -> None:
        if self.access_token_expired:
            await self._login_with_api_key()
