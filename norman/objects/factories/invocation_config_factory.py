from norman_utils_external.singleton import Singleton

from norman.helpers.input_source_resolver import InputSourceResolver
from norman.objects.configs.invocation_config import InvocationConfig


class InvocationConfigFactory(metaclass=Singleton):

    @staticmethod
    def create(invocation_config: InvocationConfig) -> InvocationConfig:
        for input_cfg in invocation_config.inputs:
            if input_cfg.source is None:
                input_cfg.source = InputSourceResolver.resolve(input_cfg.data)
        return invocation_config
