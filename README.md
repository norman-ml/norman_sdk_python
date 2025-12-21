# Norman SDK Overview

Welcome to the Norman SDK - the developer toolkit for interacting with the Norman AI platform.

Norman SDK offers a clean, intuitive interface for uploading and invoking AI models.

Designed for developers, researchers, and production pipelines,
the Norman SDK abstracts away the complexity of Norman’s microservices
and gives you a powerful, ergonomic API for all model operations.

---

## Purpose

The Norman SDK is built to make interacting with the Norman platform simple and safe.

It provides:
- Easy model upload workflows
- Smooth invocation of deployed models
- Account and workspace management
- Built-in streaming support for inputs and outputs
- Automatic authentication handling
- High-level wrappers around all Norman services
- You get all the power of the platform with minimal boilerplate.

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

- **account** (`dict`) — Account metadata containing the following fields:
      - **id** (`str`) — Unique account identifier.  
      - **creation_time** (`datetime`) — Account creation timestamp (UTC).  
      - **name** (`str`) — Account display name.

- **api_key** (`str`) — Generated API key used to authenticate SDK requests.


> ⚠️ **Important:**  
> Store your API key securely.  
> API keys **cannot be regenerated** — if you lose yours, you’ll need to create a new account.
