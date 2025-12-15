# Norman SDK Overview

Welcome to the Norman SDK — the developer toolkit for interacting with the Norman AI platform.

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
