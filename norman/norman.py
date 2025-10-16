from contextlib import asynccontextmanager
from typing import Any

from norman_core.clients.http_client import HttpClient
from norman_objects.shared.models.model import Model

from norman.helpers.model_factory import ModelFactory
from norman.managers.authentication_manager import AuthenticationManager
from norman.managers.invocation_manager import InvocationManager
from norman.managers.model_upload_manager import ModelUploadManager
from norman.objects.configs.invocation_config import InvocationConfig


class Norman:
    def __init__(self, api_key: str):
        self._authentication_manager = AuthenticationManager(api_key)

    @staticmethod
    async def signup(username: str, password: str) -> dict[str, Any]:
        return await AuthenticationManager.signup_with_password(username, password)

    async def invoke(self, invocation_config: InvocationConfig) -> dict[str, bytearray]:
        async with self._get_http_client() as http_client:
            invocation = await InvocationManager.create_invocation_in_database(http_client, self._authentication_manager.access_token, invocation_config)
            await InvocationManager.upload_inputs(http_client, self._authentication_manager.access_token, invocation, invocation_config)
            await InvocationManager.wait_for_flags(http_client, self._authentication_manager.access_token, invocation)
            return await InvocationManager.get_results(http_client, self._authentication_manager.access_token, invocation)

    async def upload_model(self, model_config: dict[str, Any]) -> Model:
        async with self._get_http_client() as http_client:
            model = ModelFactory.create_model(self._authentication_manager.account_id, model_config)
            model = await ModelUploadManager.upload_model(http_client, self._authentication_manager.access_token, model)
            await ModelUploadManager.upload_assets(http_client, self._authentication_manager.access_token, model, model_config["assets"])
            await ModelUploadManager.wait_for_flags(http_client, self._authentication_manager.access_token, model)
            return model

    @asynccontextmanager
    async def _get_http_client(self, login=True):
        http_client = HttpClient()
        if login and self._authentication_manager.access_token_expired:
            await self._authentication_manager.login_internal()
        yield http_client
        await http_client.close()
