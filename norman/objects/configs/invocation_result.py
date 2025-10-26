from typing import Any


class InvocationResult:
    def __init__(self, outputs: dict[str, "InvocationOutputHandle"]):
        self._outputs = outputs

    def __getitem__(self, key: str) -> "InvocationOutputHandle":
        return self._outputs[key]

    async def json(self) -> dict[str, Any]:
        result = {}
        for key, handle in self._outputs.items():
            result[key] = await handle.json()
        return result

    def keys(self):
        return self._outputs.keys()

    def values(self):
        return self._outputs.values()

    def items(self):
        return self._outputs.items()
