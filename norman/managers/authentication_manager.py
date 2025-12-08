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
    """
    Centralized authentication handler for the Norman SDK. This manager
    handles API-key–based authentication, token refresh, and storage of
    identity metadata such as the authenticated user's `account_id`.

    The manager maintains secure references to access tokens and ID tokens,
    automatically refreshes expired credentials, and exposes helper methods
    used throughout the SDK for authenticated operations.

    Authentication follows this sequence:

    - User provides an API key via `set_api_key()`
    - The manager performs an API-key login using the `Authenticate` service
    - Access and ID tokens are stored as `Sensitive[str]`
    - Tokens are automatically refreshed when expired

    **Methods**
    """

    def __init__(self) -> None:
        self._authentication_service = Authenticate()
        self._http_client = HttpClient()

        self._api_key = None
        self._account_id = None
        self._access_token: Optional[Sensitive[str]] = None
        self._id_token: Optional[Sensitive[str]] = None

    @property
    def access_token(self) -> Sensitive[str]:
        """
        Retrieve the currently stored access token.

        **Returns**

        - **Sensitive[str]**
            The active access token.

        **Raises**

        - **ValueError**
            If no token has been obtained yet (user not logged in).
        """
        if self._access_token is None:
            raise ValueError("Access token is not available — you may need to log in first")
        return self._access_token

    @property
    def account_id(self) -> Optional[str]:
        """
        Retrieve the authenticated user's account ID.

        **Returns**

        - **str | None**
            Account ID if logged in, otherwise `None`.
        """
        return self._account_id

    def set_api_key(self, api_key: str) -> None:
        """
        Store the API key that will be used to authenticate the user.

        **Parameters**

        - **api_key** (`str`)
            The API key issued to the user.
        """
        self._api_key = api_key

    def access_token_expired(self) -> bool:
        """
        Determine whether the current access token is expired.

        Token expiration is computed by decoding the JWT without signature
        verification (signature verification will be added once JWKS
        support is enabled).

        **Returns**

        - **bool**
            `True` if the access token is missing or expired; otherwise `False`.
        """
        if self._access_token is None:
            return True
        try:
            decoded = jwt.decode(
                self._access_token.value(),
                options={"verify_signature": False}
            )
            exp = decoded["exp"]
            now = datetime.now(timezone.utc).timestamp()
            return exp < now
        except Exception:
            return True

    @staticmethod
    async def signup_and_generate_key(username: str) -> SignupKeyResponse:
        """
        **Coroutine**

        Register a new account and generate an API key for the user.

        This static method exists because signup does not require an existing
        authenticated session.

        **Parameters**

        - **username** (`str`)
            Name to associate with the new account.

        **Returns**

        - **SignupKeyResponse**
            Contains the generated API key and signup metadata.
        """
        async with HttpClient():
            authentication_service = Authenticate()
            signup_request = SignupKeyRequest(name=username)
            signup_response = await authentication_service.signup.signup_and_generate_key(signup_request)
            return signup_response

    async def _login_with_api_key(self) -> None:
        """
        **Coroutine**

        Perform an API-key-based login to obtain access and ID tokens.

        This method is invoked internally whenever a valid session is required
        but the stored token is missing or expired.

        **Raises**

        - **ValueError**
            If an API key has not been provided via `set_api_key()`.
        """
        async with self._http_client:
            if self._api_key is None or self._api_key == "":
                raise ValueError("API key is required. Please provide a valid API key")

            login_request = ApiKeyLoginRequest(api_key=Sensitive(self._api_key))
            login_response = await self._authentication_service.login.login_with_key(login_request)

            self._account_id = login_response.account.id
            self._access_token = login_response.access_token
            self._id_token = login_response.id_token

    async def invalidate_access_token(self) -> None:
        """
        **Coroutine**

        Ensure that the current access token is valid. If the token is expired
        or missing, this method will automatically trigger a fresh login using
        the stored API key.

        **Returns**

        - **None**
        """
        if self.access_token_expired:
            await self._login_with_api_key()
