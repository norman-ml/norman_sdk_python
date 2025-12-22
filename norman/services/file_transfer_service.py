import io
import json
from pathlib import Path
from typing import Any, Union

import aiofiles
from norman_core.clients.socket_client import SocketClient
from norman_core.services.file_push.file_push import FilePush
from norman_objects.services.file_push.checksum.checksum_request import ChecksumRequest
from norman_objects.services.file_push.pairing.socket_asset_pairing_request import SocketAssetPairingRequest
from norman_objects.services.file_push.pairing.socket_input_pairing_request import SocketInputPairingRequest
from norman_objects.shared.security.sensitive import Sensitive
from norman_utils_external.singleton import Singleton


class FileTransferService(metaclass=Singleton):
    def __init__(self) -> None:
        self._file_push_service = FilePush()

    async def upload_file(self, token: Sensitive[str], pairing_request: Union[SocketAssetPairingRequest, SocketInputPairingRequest], path: Union[str, Path]) -> None:
        async with aiofiles.open(path, mode="rb") as file:
            await self.upload_from_buffer(token, pairing_request, file)

    async def upload_file_with_version_id(self, token: Sensitive[str], pairing_request: SocketAssetPairingRequest, path: Union[str, Path], version_id: str) -> None:
        """Upload file with version_id added to the JSON payload (workaround for missing field in model)"""
        async with aiofiles.open(path, mode="rb") as file:
            await self.upload_from_buffer_with_version_id(token, pairing_request, file, version_id)

    async def upload_from_buffer(self, token: Sensitive[str], pairing_request: Union[SocketAssetPairingRequest, SocketInputPairingRequest], buffer: Union[bytes, io.BytesIO]) -> None:
        if isinstance(pairing_request, SocketAssetPairingRequest):
            socket_info = await self._file_push_service.allocate_socket_for_asset(token, pairing_request)
        elif isinstance(pairing_request, SocketInputPairingRequest):
            socket_info = await self._file_push_service.allocate_socket_for_input(token, pairing_request)
        else:
            raise TypeError("Unsupported pairing request type")

        checksum = await SocketClient.write_and_digest(socket_info, buffer)
        checksum_request = ChecksumRequest(pairing_id=socket_info.pairing_id, checksum=checksum)
        await self._file_push_service.complete_file_transfer(token, checksum_request)

    async def upload_from_buffer_with_version_id(self, token: Sensitive[str], pairing_request: SocketAssetPairingRequest, buffer: Union[bytes, io.BytesIO], version_id: str) -> None:
        """Upload from buffer with version_id added to JSON payload"""
        # Get the base JSON payload
        json_payload = pairing_request.model_dump(mode="json")
        # Add version_id which is missing from the model definition
        json_payload["version_id"] = version_id
        
        # Call the HTTP client directly with the modified JSON
        from norman_core.clients.http_client import HttpClient
        http_client = HttpClient()
        response = await http_client.post("file-push/socket/pair/asset", token, json=json_payload)
        from norman_objects.services.file_push.pairing.socket_pairing_response import SocketPairingResponse
        socket_info = SocketPairingResponse.model_validate(response)

        checksum = await SocketClient.write_and_digest(socket_info, buffer)
        checksum_request = ChecksumRequest(pairing_id=socket_info.pairing_id, checksum=checksum)
        await self._file_push_service.complete_file_transfer(token, checksum_request)

    def normalize_primitive_data(self, data: Any) -> io.BytesIO:
        if isinstance(data, str):
            return io.BytesIO(data.encode("utf-8"))

        elif isinstance(data, (bytes, bytearray)):
            return io.BytesIO(data)

        elif isinstance(data, io.BytesIO):
            return data

        elif isinstance(data, (int, float)):
            return io.BytesIO(str(data).encode("utf-8"))

        elif isinstance(data, (dict, list)):
            json_str = json.dumps(data)
            return io.BytesIO(json_str.encode("utf-8"))

        else:
            raise ValueError(f"Unsupported data type: {type(data)}. Cannot convert to BytesIO.")
