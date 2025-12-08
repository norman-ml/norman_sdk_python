from norman_objects.shared.model_signatures.http_location import HttpLocation
from norman_objects.shared.model_signatures.model_signature import ModelSignature
from norman_objects.shared.model_signatures.signature_type import SignatureType
from norman_utils_external.singleton import Singleton

from norman.objects.configs.model.signature_config import SignatureConfig
from norman.objects.factories.parameter_factory import ParameterFactory
from norman.resolvers.signature_modality_resolver import SignatureModalityResolver


class SignatureFactory(metaclass=Singleton):
    """
    Factory responsible for constructing `ModelSignature` objects from the
    high-level declarative `SignatureConfig`. The factory resolves encoding,
    modality, HTTP binding location, parameters, and defaults, producing a
    strongly typed signature definition used when registering and executing
    models.

    Signatures describe how models receive and produce data, including:

    - Data modality (audio, text, image, etc.)
    - Data domain (semantic grouping)
    - Encoding type
    - HTTP location (body, query, etc.)
    - Parameters and sub-fields
    - Optional metadata such as visibility and default values

    **Methods**
    """

    @staticmethod
    def create(signature_config: SignatureConfig, signature_type: SignatureType) -> ModelSignature:
        """
        Create a `ModelSignature` object from a `SignatureConfig`, assigning the
        appropriate signature type (input/output) and resolving all fields into
        their normalized forms.

        **Behavior Summary**

        - Resolves the signature’s data modality based on the declared encoding
          using `SignatureModalityResolver`.
        - Determines correct `http_location`, defaulting to `HttpLocation.Body`
          when unspecified.
        - Normalizes `hidden` and `default_value` fields.
        - Builds signature parameters using `ParameterFactory`.
        - Initializes empty transform and argument lists (reserved for future
          extensibility).

        **Parameters**

        - **signature_config** (`SignatureConfig`)
            Declarative configuration describing the signature’s structure,
            encoding, metadata, and optional parameters.

        - **signature_type** (`SignatureType`)
            Indicates whether this signature represents a model input or output.

        **Returns**

        - **ModelSignature**
            A fully constructed signature definition describing how a model
            expects or produces data.

        **Raises**

        - **ValueError**
            If the data encoding is unknown or cannot be resolved.
        """
        data_modality = SignatureModalityResolver.resolve(signature_config.data_encoding)

        http_location = HttpLocation.Body
        if signature_config.http_location is not None:
            http_location = signature_config.http_location

        hidden = False
        if signature_config.hidden is not None:
            hidden = signature_config.hidden

        default_value = None
        if signature_config.default_value is not None:
            default_value = signature_config.default_value

        parameters = []
        for parameter in signature_config.parameters:
            parameters.append(ParameterFactory.create(parameter))

        # Currently not defined by users, defined for completeness
        transforms = []
        signature_args = {}

        model_signature = ModelSignature(
            signature_type=signature_type,
            data_modality=data_modality,
            data_domain=signature_config.data_domain,
            data_encoding=signature_config.data_encoding,
            receive_format=signature_config.receive_format,
            http_location=http_location,
            hidden=hidden,
            display_title=signature_config.display_title,
            default_value=default_value,
            parameters=parameters,
            transforms=transforms,
            signature_args=signature_args
        )

        return model_signature
