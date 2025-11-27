import io
import json
from typing import Any, Union

import aiofiles
from norman_core.clients.socket_client import SocketClient
from norman_core.services.file_pull.file_pull import FilePull
from norman_core.services.file_push.file_push import FilePush
from norman_objects.services.file_push.checksum.checksum_request import ChecksumRequest
from norman_objects.services.file_push.pairing.socket_asset_pairing_request import SocketAssetPairingRequest
from norman_objects.services.file_push.pairing.socket_input_pairing_request import SocketInputPairingRequest
from norman_objects.shared.security.sensitive import Sensitive
from norman_utils_external.file_utils import FileUtils
from norman_utils_external.singleton import Singleton


class FileTransferManager(metaclass=Singleton):
    def __init__(self) -> None:
        self._file_push_service = FilePush()
        self._file_pull_service = FilePull()
        self._file_utils = FileUtils()

    async def upload_primitive(self, token: Sensitive[str], pairing_request: Union[SocketAssetPairingRequest, SocketInputPairingRequest], data: Any) -> None:
        if isinstance(data, (bytes, bytearray)):
            payload = data
        elif isinstance(data, (dict, list)):
            payload = json.dumps(data).encode()
        else:
            payload = str(data).encode()
        buffer = io.BytesIO(payload)
        await self.upload_from_buffer(token, pairing_request, buffer)

    async def upload_file(self, token: Sensitive[str], pairing_request: Union[SocketAssetPairingRequest, SocketInputPairingRequest], path: str) -> None:
        async with aiofiles.open(path, mode="rb") as file:
            await self.upload_from_buffer(token, pairing_request, file)

    async def upload_from_buffer(self, token: Sensitive[str], pairing_request: Union[SocketAssetPairingRequest, SocketInputPairingRequest], buffer: Any) -> None:
        file_size = self._file_utils.get_buffer_size(buffer)
        pairing_request.file_size_in_bytes = file_size
        if isinstance(pairing_request, SocketAssetPairingRequest):
            socket_info = await self._file_push_service.allocate_socket_for_asset(token, pairing_request)
        elif isinstance(pairing_request, SocketInputPairingRequest):
            socket_info = await self._file_push_service.allocate_socket_for_input(token, pairing_request)
        else:
            raise TypeError("Unsupported pairing request type Expected SocketAssetPairingRequest or SocketInputPairingRequest.")

        checksum = await SocketClient.write_and_digest(socket_info, buffer)
        checksum_request = ChecksumRequest(pairing_id=socket_info.pairing_id, checksum=checksum)
        await self._file_push_service.complete_file_transfer(token, checksum_request)
