from typing import Any

from norman_objects.shared.models.model import Model
from norman_utils_external.singleton import Singleton

from norman.managers.authentication_manager import AuthenticationManager
from norman.managers.invocation_manager import InvocationManager
from norman.managers.model_upload_manager import ModelUploadManager


class Norman(metaclass=Singleton):
    """
    Core entry point for interacting with the Norman SDK.

    The `Norman` class provides a unified interface for all SDK operations,
    including authentication, model uploads, and model invocations.

    It manages internal authentication and service communication automatically
    once initialized with a valid API key.

    Example:
        ```python
        from norman import Norman

        norman = Norman(api_key="nrm_sk_...")
        model = await norman.upload_model(model_config)
        results = await norman.invoke(invocation_config)
        ```
    """

    def __init__(self, api_key: str):
        """
        Initialize the Norman SDK instance.

        Args:
            api_key (str): The API key used to authenticate all SDK operations.

        Notes:
            - The API key is provided when you sign up using `Norman.signup()`.
            - The SDK automatically injects this key into all outgoing requests.
        """
        self._authentication_manager = AuthenticationManager()
        self._authentication_manager.set_api_key(api_key)
        self._invocation_manager = InvocationManager()
        self._model_upload_manager = ModelUploadManager()

    @staticmethod
    async def signup(username: str) -> dict[str, Any]:
        """
        **Coroutine**

        Create a new Norman account and generate a unique API key.

        This method registers a new user and returns their account details
        along with a freshly generated API key for SDK authentication.

        **Parameters**

        - ***username*** (`str`) - The username or email address to register.
          Must be unique across the Norman platform.

        **Response Structure**

        - ***response*** (`dict[str, Any]`) - Dictionary containing account metadata and the generated API key.

            - **account** (`dict`) - Metadata of the created account.
                - **id** (`str`) - Unique account identifier.
                - **creation_time** (`datetime`) - Account creation timestamp (UTC).
                - **name** (`str`) - Display name of the registered account.

            - **api_key** (`str`) - The generated API key used for authenticating SDK requests.

        **Example Usage:**
        ```python
        response = await Norman.signup("alice@example.com")
        api_key = response["api_key"]
        ```

        **Response Example:**
        ```python
        {
            "account": {
                "id": "23846818392186611174803470025142422015",
                "creation_time": "2025-11-09T14:22:17Z",
                "name": "Alice Johnson"
            },
            "api_key": "nrm_sk_2a96b7b1a9f44b09b7c3f9f1843e93e2"
        }
        ```

        > ⚠️ **Important:**
        > Store your API key securely.
        > API keys **cannot be regenerated** — if you lose yours, you’ll need to create a new account.
        """
        return await AuthenticationManager.signup_and_generate_key(username)


    async def upload_model(self, model_config: dict[str, Any]) -> Model:
        """
        **Coroutine**

        Upload and register a new model on the Norman platform.

        This method uploads the model metadata, assets, and input/output signatures
        defined in the provided `model_config`. It returns a `Model` object
        containing the registered model’s metadata and deployment details.

        **Parameters**

        - ***model_config*** (`dict[str, Any]`) — Configuration matching the `ModelConfig` schema.
          Defines the model’s metadata, assets, inputs, outputs, and deployment attributes.

            **Root object (`dict`):**

            - **name** (`str`) — Unique name of the model.

            - **version_label** (`str`) — Human-readable version label (e.g., `"v1.0"`, `"beta"`).

            - **short_description** (`str`) — Concise summary of what the model does.

            - **long_description** (`str`) — Detailed explanation of the model, usage, and behavior.

            - **inputs** (`List[dict]`) — Input signatures defining model inputs and their formats.
                - **display_title** (`str`) — Human-readable name for the input.
                - **data_encoding** (`str`) — Encoding format for input data (e.g., `"UTF-8"`, `"binary"`).
                - **receive_format** (`str`) — Expected input type (e.g., `"File"`, `"Link"`, `"Primitive"`).
                - **parameters** (`List[dict]`) — Parameter definitions with:
                    - **parameter_name** (`str`) — Name of the parameter.
                    - **data_encoding** (`str`) — Encoding used for that parameter (e.g., `"float32"`).
                - **http_location** (`Optional[str]`) — Optional HTTP field location (`"Body"`, `"Path"`, `"Query"`).
                - **hidden** (`Optional[bool]`) — If `True`, hides this field in public interfaces.
                - **default_value** (`Optional[str]`) — Default value if not explicitly provided.

            - **outputs** (`List[dict]`) —
              Output signatures defining model outputs and their formats.
              Structure mirrors `inputs`.

            - **assets** (`List[dict]`) — List of assets (e.g., model weights, tokenizer files, configs).
                - **asset_name** (`str`) — Identifier for the asset (e.g., `"weights"`, `"tokenizer"`).
                - **data** (`Any`) — Asset content or reference (local path, URL, or binary).
                - **source** (`Optional[str]`) — Origin of the asset (`"File"`, `"Link"`, `"Primitive"`).

            - **output_format** (`Optional[str]`) —
              Desired model output format (`"JSON"`, `"Binary"`).

            - **model_type** (`Optional[str]`) —
              Model type or framework (`"PyTorch"`, `"TensorFlow"`, etc.).

            - **request_type** (`Optional[str]`) —
              HTTP request type used for inference (`"POST"`, `"GET"`).

            - **model_class** (`Optional[str]`) —
              Fully qualified class name or identifier for the model implementation.

            - **hosting_location** (`Optional[str]`) —
              Where the model will be hosted (`"Internal"`, `"External"`).

            - **url** (`Optional[str]`) —
              External URL for models hosted outside Norman (required for external models).

        **Response Structure**

        - ***response*** (`Model`) —
          A `Model` object containing metadata for the uploaded model.

            - **name** (`str`) — Model name.
            - **model_id** (`str`) — Unique identifier assigned by Norman.
            - **url** (`str`) — API endpoint for invoking the model.
            - **model_type** (`str`) — Model framework type.
            - **hosting_location** (`str`) — Where the model is hosted.
            - **inputs / outputs** (`List[dict]`) — Model I/O signatures.

        **Example Usage:**
        ```python
        model_config = {
            "name": "image_reverser_model",
            "version_label": "beta",
            "short_description": "A simple model that mirrors images.",
            "long_description": "Demonstrates image reversal for onboarding.",
            "assets": [
                {"asset_name": "weights", "data": "./model.pt"}
            ],
            "inputs": [
                {
                    "display_title": "Input Image",
                    "data_encoding": "png",
                    "receive_format": "File",
                    "parameters": [{"parameter_name": "image", "data_encoding": "png"}]
                }
            ],
            "outputs": [
                {
                    "display_title": "Output Image",
                    "data_encoding": "png",
                    "receive_format": "File",
                    "parameters": [{"parameter_name": "mirror_image", "data_encoding": "png"}]
                }
            ]
        }

        norman = Norman(api_key="nrm_sk_...")
        model = await norman.upload_model(model_config)
        print("Model uploaded successfully:", model.name)
        ```

        > ⚠️ **Important:**
        > Ensure that all assets referenced in `model_config["assets"]` are accessible.
        > Invalid file paths or missing URLs will cause upload errors.
        """
        return await self._model_upload_manager.upload_model(model_config)


    async def invoke(self, invocation_config: dict[str, Any]) -> dict[str, bytearray]:
        """
        **Coroutine**

        Invoke a model and retrieve its outputs.

        This method executes a deployed Norman model using the provided
        `invocation_config`. The configuration describes which model to run,
        what inputs to send, and how outputs should be returned.

        **Parameters**

        - ***invocation_config*** (`dict[str, Any]`) - Configuration matching the `InvocationConfig` schema.

            - **model_name** (`str`) - Name or unique identifier of the model to invoke.

            - **inputs** (`List[dict]`) - List of model inputs, each describing one input parameter.

                - **display_title** (`str`) – Human-readable label (e.g., `"Input image"`).
                - **data** (`Any`) – The actual payload (path, bytes, or text).
                  - **source** (`str`, `Optional`) – Where the input comes from (`"File"`, `"Link", `"Primitive" or `"Stream"`)

            - **outputs_format** (`Optional[dict[str, str]]`) - Mapping of output names to desired formats, key is the output name and value is the desired format(`"bytes"` or `"stream"`)

        **Response Structure**

        - ***response*** (`dict[str, bytearray]`) - A mapping of output names to their binary results.

        **Output Example:**
        ```python
        {
            "output_image": b"<binary bytes>"
        }
        ```

        Example:
            ```python
            results = await norman.invoke({
                "model_name": "image_reverser_model28",
                "inputs": [
                    {
                        "display_title": "Input",
                        "data": "/path/to/image.png",
                        "source": "File"
                    }
                ],
                "outputs_format": {
                    "Output": "bytes"
                }
            })

            data = results["Output"]
            with open("result.png", "wb") as f:
                f.write(data)
            ```
        """
        return await self._invocation_manager.invoke(invocation_config)


