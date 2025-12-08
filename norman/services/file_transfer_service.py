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
    """
    High-level service responsible for uploading files, buffers, and primitive
    data to Norman's file-push pipeline. This service coordinates with
    `FilePush` to allocate file-transfer sockets and uses `SocketClient` to
    stream data while computing checksums for integrity verification.

    Supports:
    - Uploading files from disk
    - Uploading in-memory byte streams
    - Uploading primitive values normalized into bytes (strings, numbers, dicts, lists)

    **Constructor**

    Initializes the file-push integration by creating an internal `FilePush`
    service instance. Because the class is implemented as a singleton, the
    same file-push client is reused for all transfers, improving connection
    reuse and reducing overhead.

    **Methods**
    """

    def __init__(self) -> None:
        self._file_push_service = FilePush()

    async def upload_file(
        self,
        token: Sensitive[str],
        pairing_request: Union[SocketAssetPairingRequest, SocketInputPairingRequest],
        path: Union[str, Path]
    ) -> None:
        """
        **Coroutine**

        Upload a file from disk by streaming its contents through a
        file-transfer socket allocated by the server. The file is opened
        asynchronously and forwarded to `upload_from_buffer()`.

        **Parameters**

        - **token** (`Sensitive[str]`)
            Authentication token authorizing the file-push operation.

        - **pairing_request**
          (`Union[SocketAssetPairingRequest, SocketInputPairingRequest]`)
            Data describing where this file should be routed (asset upload or
            invocation input upload).

        - **path** (`str | Path`)
            Filesystem path pointing to the file to upload.

        **Returns**

        - **None**

        **Raises**

        - **FileNotFoundError** — If the path does not exist.
        - **PermissionError** — If the file cannot be opened for reading.
        """
        async with aiofiles.open(path, mode="rb") as file:
            await self.upload_from_buffer(token, pairing_request, file)

    async def upload_from_buffer(
        self,
        token: Sensitive[str],
        pairing_request: Union[SocketAssetPairingRequest, SocketInputPairingRequest],
        buffer: Union[bytes, io.BytesIO]
    ) -> None:
        """
        **Coroutine**

        Upload data from an in-memory buffer over a socket allocated by the
        `FilePush` service. After sending the data, a checksum is computed and
        transmitted to the server to finalize the transfer.

        **Parameters**

        - **token** (`Sensitive[str]`)
            Authentication token authorizing the file-push operation.

        - **pairing_request**
          (`Union[SocketAssetPairingRequest, SocketInputPairingRequest]`)
            Determines whether the upload relates to an asset or a model input.

        - **buffer** (`bytes | io.BytesIO`)
            The in-memory data to stream.

        **Returns**

        - **None**

        **Raises**

        - **TypeError** — If the pairing request type is not supported.
        - **ValueError** — If socket allocation or server operations fail.
        """
        if isinstance(pairing_request, SocketAssetPairingRequest):
            socket_info = await self._file_push_service.allocate_socket_for_asset(token, pairing_request)
        elif isinstance(pairing_request, SocketInputPairingRequest):
            socket_info = await self._file_push_service.allocate_socket_for_input(token, pairing_request)
        else:
            raise TypeError("Unsupported pairing request type")

        checksum = await SocketClient.write_and_digest(socket_info, buffer)
        checksum_request = ChecksumRequest(pairing_id=socket_info.pairing_id, checksum=checksum)
        await self._file_push_service.complete_file_transfer(token, checksum_request)

    def normalize_primitive_data(self, data: Any) -> io.BytesIO:
        """
        Normalize a primitive Python value or structure into an in-memory
        `BytesIO` buffer suitable for upload through the file-push pipeline.

        Supported conversions:

        - `str` - UTF-8 encoded bytes  
        - `bytes` / `bytearray` - Returned as-is  
        - `BytesIO` - Returned unchanged  
        - `int` / `float` - Stringified and encoded as UTF-8  
        - `dict` / `list` - JSON-encoded UTF-8 bytes  

        **Parameters**

        - **data** (`Any`)
            The value to convert into a buffer.

        **Returns**

        - **BytesIO**
            A binary buffer representation of the value.

        **Raises**

        - **ValueError**
            If the value cannot be converted into binary form.
        """
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
