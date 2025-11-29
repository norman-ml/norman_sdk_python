from typing import Any

from norman_objects.shared.models.model import Model
from norman_utils_external.singleton import Singleton

from norman.managers.authentication_manager import AuthenticationManager
from norman.managers.invocation_manager import InvocationManager
from norman.managers.model_upload_manager import ModelUploadManager


class Norman(metaclass=Singleton):
    def __init__(self, api_key: str):
        self._authentication_manager = AuthenticationManager()
        self._authentication_manager.set_api_key(api_key)

        self._invocation_manager = InvocationManager()
        self._model_upload_manager = ModelUploadManager()

    @staticmethod
    async def signup(username: str) -> dict[str, Any]:
        return await AuthenticationManager.signup_and_generate_key(username)

    async def upload_model(self, model_config: dict[str, Any]) -> Model:
        return await self._model_upload_manager.upload_model(model_config)

    async def invoke(self, invocation_config: dict[str, Any]) -> dict[str, bytearray]:
        return await self._invocation_manager.invoke(invocation_config)
