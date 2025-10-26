from collections.abc import dict_keys, dict_values, dict_items
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

    def keys(self) -> dict_keys[str, Any]:
        return self._outputs.keys()

    def values(self) -> dict_values[str, Any]:
        return self._outputs.values()

    def items(self) -> dict_items[str, Any]:
        return self._outputs.items()
