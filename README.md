from tests.conftest import api_key

# Norman SDK Overview

Welcome to the Norman SDK - the developer toolkit for interacting with the Norman AI platform.

Norman SDK offers a clean, intuitive interface for uploading and invoking AI models.

Designed for developers, researchers, and production pipelines,
the Norman SDK abstracts away the complexity of running AI models
and gives you a powerful API for all model operations.

Main capabilities:
- Easy model upload workflows
- Simple invocation of deployed models
- Api key registration management

For the full reference and details instructions please visit our [Sdk Documentation](https://sdk.norman-ai.com/)

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

```python
from norman import Norman

signup_response = await Norman.signup("<username>")
api_key = signup_response.api_key 
```

> ⚠️ **Important:**  
> Store your API key securely. API keys **cannot be regenerated** - if you lose your key, you will lose access to all your data in result across norman clients.

## 3. Run your first model
With the Norman SDK, running a model is straightforward. You select a model from our [Model Library](https://norman-ai.com/library), check the required inputs and their format, and invoke the model using a simple API call.

Norman makes a distinction between deploying a model and invoking it. We call their configuration classes, respectively, the Model config and the Invocation config.

---

### Define an invocation configuration
Model owners define what is called the model signature when deploying to Norman. A model signature consists of input and output signatures, which collectively define how Norman should transform user input so the model can run it and vice versa.

To run a model we must first define an invocation configuration object, defining how our input data maps to the model input signature:

In this example we will define a configuration object for an image generation model called Stable Diffusion 3.5 Large. This particular model expects one text input from the user to be mapped to the "Prompt" parameter in the model:

```python
# define an invocation configuration object
invocation_config = {
    "model_name": "stable-diffusion-3.5-large",
    "inputs": [
        {
            "display_title": "Prompt",
            "data": "A cat playing with a ball on Mars"
        }
    ]
}
```

### Invoke the model
Running a model is an asynchronous process that can take several minutes to complete, the duration depends on the model size, the input size and the load on the Norman service.  

For more granular control and advanced configuration options, please have a look at the [Norman Core SDK documentation](https://sdk.norman-ai.com/api/core/overviewcore/overviewcore).
```python
from norman import Norman

# Initialize the SDK with your API key
norman = Norman(api_key="fQraVxLczNA4h01XWnjRT6Cpux-45Cdf5oZMbaCJ7pEDzXpqPIwMaDotq8VlqiG718iRf4DhyUJqGLJoe3lkSIsqfrgFFolvY6Bd0L4WDLQZLlks")

# Invoke the model
invocation_response = await norman.invoke(invocation_config)
```

---

### Use the model outputs
Each model uploaded to Norman has a unique output signature. When you invoke a model, the response is returned according to the structure of the output signature, formatted as a dictionary.

- Dictionary keys each map to an output display title
- Values are binary byte streams encoding the model output.

Output values can be consumed and used in a variety of ways, according to the needs of each user. Stable Diffusion 3.5 Large exposes one output parameter called called "Image" which users can comsume:

```python
from io import BytesIO
from PIL import Image

# Get the raw image bytes from the response
image_bytes = invocation_response["Image"]

# Load the image from memory
image = Image.open(BytesIO(image_bytes))
image.show(title="stable-diffusion-3.5-large output image")

# Optionally save the image to disk
image.save("stable_diffusion_3_5_large_output_image.png")

```
---

## 4. Optional - Upload your own model

Norman provides a large selection of ready to run AI models. If you want to deploy your own model, you can provide the model files, define the input and output signatures and configure the user interface. 

You can use the SDK to deploy your model to the Norman servers, letting you run it just as you would run any other model in the model library.

---

### Example: Uploading a Text to Image Model

Below is a complete example of uploading a simple text to image model.
The model accepts a text prompt and returns an image.

For more details visit [Norman SDK upload model documentation](https://sdk.norman-ai.com/api/norman1/overview1#3)

### Define a Model Configuration
The model configuration defines how your model is registered and exposed within Norman.
It describes the model’s metadata, assets, and its expected inputs and outputs.

At a high level, a model configuration includes:

- Basic information
such as the model name, version label, and descriptions that appear in the Models Library.

- Assets
References to model files (for example weights) that Norman will store and make available at runtime.

- Input signatures - a structured definition of what inputs the model expects, including display titles shown to users, data encodings (e.g. txt, png) and parameter mappings used internally by the model

- Output signatures - a definition of what the model returns, including output names exposed to users, data formats and encodings and whether the output is returned as a primitive value or a file

This configuration allows Norman to validate inputs, transform data and allow users to invoke your model.
```python
model_config = {
    "name":"stable-diffusion-3.5-large",
    "category":"diffusion",
    "version":{
        "label":"beta",
        "short_description": "A text-to-image diffusion model for high-quality image generation.",
        "long_description": (
            "Stable Diffusion 3.5 large is a latent text-to-image diffusion model trained on "
            "a large-scale dataset to generate detailed and diverse images from natural "
            "language prompts. It serves as a general-purpose foundation model that can "
            "be fine-tuned for tasks such as image generation, editing, and style transfer."
        ),    
        "assets":[
            {
                "asset_name":"File",
                "data":"<path/to/your/file>"
            },
            {
                "asset_name":"Logo",
                "data":"<path/to/your/file>"
            }
        ],
        "inputs":[
            {
                "display_title":"Prompt",
                "data_modality":"Text",
                "data_domain":"prompt",
                "data_encoding":"utf8",
                "receive_format":"primitive",
                "parameters":[
                    {
                        "parameter_name":"prompt",
                        "data_encoding":"utf8"
                    }
                ]
            }
        ],
        "outputs":[
            {
                "display_title":"Image",
                "data_modality":"image",
                "data_domain":"generate_image",
                "data_encoding":"png",
                "receive_format":"File",
                "parameters":[
                    {
                        "parameter_name":"image",
                        "data_encoding":"png"
                    }
                ]
            }
        ]
    }
}
```

### Upload the Model
Once the model configuration is defined, uploading the model is a single API call.
During upload, Norman:

- Stores the model assets securely

- Registers the input and output signatures

- Makes the model available in your Models Library

- Deploys the model for immediate invocation

```python
from norman import Norman

norman = Norman(api_key="fQraVxLczNA4h01XWnjRT6Cpux-45Cdf5oZMbaCJ7pEDzXpqPIwMaDotq8VlqiG718iRf4DhyUJqGLJoe3lkSIsqfrgFFolvY6Bd0L4WDLQZLlks")

model = await norman.upload_model(model_config)
```

## What Happens After Uploading?

Once the model is uploaded:
- Norman stores your assets securely.
- The model becomes visible in your Models Library.
- You can invoke it immediately using:
```python
response = await norman.invoke({
    "model_name": "stable-diffusion-3.5-large",
    "inputs": [
        {
            "display_title": "Prompt",
            "data": "A cat playing with a ball on mars"
        }
    ]
})
```

