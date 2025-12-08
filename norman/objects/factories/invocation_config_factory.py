from typing import Any

from norman_utils_external.singleton import Singleton

from norman.objects.configs.invocation.invocation_config import InvocationConfig
from norman.resolvers.input_source_resolver import InputSourceResolver


class InvocationConfigFactory(metaclass=Singleton):
    """
    Factory responsible for constructing a fully populated `InvocationConfig`
    object from raw dictionary input. This includes validating the configuration
    using Pydantic and automatically inferring input sources when not explicitly
    provided.

    This utility ensures consistent preprocessing of invocation metadata before
    execution by normalizing input definitions and applying SDK-level defaults.

    **Methods**
    """

    @staticmethod
    def create(invocation_config: dict[str, Any]) -> InvocationConfig:
        """
        Create and normalize an `InvocationConfig` from a raw dictionary of
        invocation parameters. The method validates the configuration using
        the Pydantic model and automatically resolves missing input sources
        using `InputSourceResolver`.

        **Parameters**

        - **invocation_config** (`dict[str, Any]`)
            A raw dictionary representation of an invocation configuration.
            Must follow the schema expected by `InvocationConfig`.

        **Returns**

        - **InvocationConfig**
            A validated and normalized invocation configuration. Any input whose
            `source` field was originally `None` will have its source inferred
            based on the provided data (e.g., file path, URL, primitive value).

        **Raises**

        - **pydantic.ValidationError**
            If the provided dictionary does not conform to the `InvocationConfig`
            schema.
        """
        invocation_config = InvocationConfig.model_validate(invocation_config)

        for invocation_input in invocation_config.inputs:
            if invocation_input.source is None:
                invocation_input.source = InputSourceResolver.resolve(invocation_input.data)

        return invocation_config
