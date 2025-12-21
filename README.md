# Norman SDK Overview

Welcome to the Norman SDK - the developer toolkit for interacting with the Norman AI platform.

Norman SDK offers a clean, intuitive interface for uploading and invoking AI models.

Designed for developers, researchers, and production pipelines,
the Norman SDK abstracts away the complexity of Norman’s microservices
and gives you a powerful, ergonomic API for all model operations.

Main capabilities:
- Easy model upload workflows
- Smooth invocation of deployed models
- Account management

---

## Architecture

The Norman SDK sits on top of the Norman Core SDK.
It transforms low-level primitives into high-level developer operations.

```text
+----------------------------------------------------------+
|                     Your Application                     |
| (AI apps, pipelines, UIs, inference workers, automation) |
+------------------------------▲---------------------------+
                               │
                        uses Norman SDK
                               │
+----------------------------------------------------------+
|                         Norman SDK                       |
| (Model Upload, Invoke, Workspaces, Accounts, Utilities)  |
+------------------------------▲---------------------------+
                               │
              internally uses Norman Core SDK services
                               │
+----------------------------------------------------------+
|                    Norman Core SDK                       |
| (HttpClient, Retrieve, FilePush, FilePull, SocketClient) |
+----------------------------------------------------------+
```

# Developer Quickstart

Take your first steps with the Norman API.

---

## 1. Install the Norman SDK

To use the Norman API in Python, install the official Norman SDK using **pip**:

```bash
pip install norman
```

---

## 2. Signup and Create an API Key

Before making any requests, you’ll need to create an **API key**.  
This key authorizes your SDK to securely access the Norman API.

### Request Syntax
```python
from norman import Norman

response = await Norman.signup("<username>")
```

### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `username` | `str` | yes      | The account’s username or email address. |


### Example Response
```json
{
  "account": {
    "id": "23846818392186611174803470025142422015",
    "creation_time": "2025-11-09T14:22:17Z",
    "name": "Alice Johnson"
  },
  "api_key": "nrm_sk_2a96b7b1a9f44b09b7c3f9f1843e93e2"
}
```

### Response Structure

**Root object (`dict`):**

- **account** (`dict`) - Account metadata containing the following fields:
      - **id** (`str`) - Unique account identifier.  
      - **creation_time** (`datetime`) - Account creation timestamp (UTC).  
      - **name** (`str`) - Account display name.

- **api_key** (`str`) - Generated API key used to authenticate SDK requests.


> ⚠️ **Important:**  
> Store your API key securely.  
> API keys **cannot be regenerated** - if you lose yours, you’ll need to create a new account.


## 3. Run your first model

This example shows how to invoke an image-based model using the Norman SDK.
You provide an input image, and the model returns the processed output as raw bytes.

See all available models in the Models Library.

---

```python
from norman import Norman

# Initialize the SDK with your API key
norman = Norman(api_key="nrm_sk_2a96b7b1a9f44b09b7c3f9f1843e93e2")

# Define the invocation configuration
invocation_config = {
    "model_name": "image_reverser_model",
    "inputs": [
        {
            "display_title": "Input",
            "data": "/Users/alice/Desktop/sample_image.png"
        }
    ]
}

# Invoke the model
response = await norman.invoke(invocation_config)
```

---

### Example Response
```json
{
  "output_image": <bytes>  // binary data returned by the model
}
```

---

### Response Structure

**Root object (`dict`):**

- **output_image** (`bytes`) - Binary output data representing the model’s generated result.  

  For image models, this contains the image bytes.  
  For text or audio models, it contains the corresponding binary data.

---

### Accessing the Output

You can display, or save the output, for example:

```python
from io import BytesIO
from PIL import Image

data = response["output_image"]

# Open and display the image
img = Image.open(BytesIO(data))
img.show(title="output_image - Memory")

# Optionally save it to disk
img.save("test_memory_output_image.png")
```
## 4. Upload your first model

Uploading a model is the first step to making it available through Norman’s managed inference API.
You provide the model’s metadata, assets (such as weights), and input/output definitions - Norman handles storage, indexing, and deployment.

Once uploaded, you can run it from anywhere using the Norman SDK.

---

### Example: Uploading an Image Model

Below is a complete example of uploading a simple image reversal model.
The model accepts an image file and returns a mirrored copy.

## Step 1 - Define the Model Configuration
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
            "parameters": [
                {"parameter_name": "image", "data_encoding": "png"}
            ]
        }
    ],
    "outputs": [
        {
            "display_title": "Output Image",
            "data_encoding": "png",
            "receive_format": "File",
            "parameters": [
                {"parameter_name": "mirror_image", "data_encoding": "png"}
            ]
        }
    ]
}
```

## Step 2 - Upload the Model
```python
from norman import Norman

norman = Norman(api_key="nrm_sk_...")

model = await norman.upload_model(model_config)
print("Model uploaded successfully:", model.name)
```

## What Happens After Upload?

- Once the model is uploaded:
- Norman stores your assets securely.
- The model becomes visible in your Models Library.
- You can invoke it immediately using:
```python
response = await norman.invoke({
    "model_name": "image_reverser_model",
    "inputs": [
        {
            "display_title": "Input",
            "data": "/path/to/image.png"
        }
    ]
})
```

