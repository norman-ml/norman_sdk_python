from norman_objects.shared.parameters.model_param import ModelParam
from norman_utils_external.singleton import Singleton

from norman.objects.configs.model.parameter_config import ParameterConfig
from norman.resolvers.parameter_modality_resolver import ParameterModalityResolver


class ParameterFactory(metaclass=Singleton):
    """
    Factory responsible for constructing `ModelParam` objects based on the
    high-level `ParameterConfig` specification. The factory resolves the
    parameter’s declared data encoding into a corresponding `DataModality`,
    ensuring consistent interpretation of parameter types across the SDK.

    This factory is used during model registration to convert declarative
    configurations into strongly typed parameter definitions that the system
    can understand and validate.

    **Methods**
    """

    @staticmethod
    def create(parameter_config: ParameterConfig) -> ModelParam:
        """
        Create a `ModelParam` instance from the provided `ParameterConfig`.
        The factory determines the parameter’s modality (Audio, Image, Text,
        etc.) based on its declared encoding and populates the corresponding
        `ModelParam` fields.

        **Parameters**

        - **parameter_config** (`ParameterConfig`)
            High-level configuration describing the parameter’s name and
            declared data encoding (e.g., `"mp3"`, `"png"`, `"utf-8"`).

        **Returns**

        - **ModelParam**
            A fully initialized parameter definition containing the parameter
            name, encoding, and resolved data modality.

        **Raises**

        - **ValueError**
            If the encoding is invalid or cannot be resolved by
            `ParameterModalityResolver`.
        """
        data_modality = ParameterModalityResolver.resolve(parameter_config.data_encoding)
        model_param = ModelParam(
            data_encoding=parameter_config.data_encoding,
            parameter_name=parameter_config.parameter_name,
            data_modality=data_modality
        )

        return model_param

