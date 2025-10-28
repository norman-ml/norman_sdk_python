from norman_objects.shared.model_signatures.model_signature import ModelSignature
from norman_utils_external.singleton import Singleton

from norman.helpers.data_modality_resolver import DataModalityResolver
from norman.objects.configs.model.signature_config import SignatureConfig
from norman.objects.factories.parameter_factory import ParameterFactory
from norman_objects.shared.model_signatures.http_location import HttpLocation
from norman_objects.shared.model_signatures.signature_type import SignatureType


class SignatureFactory(metaclass=Singleton):

    @staticmethod
    def create(signature_config: SignatureConfig, signature_type: SignatureType) -> ModelSignature:
        parameters = []

        for parameter in signature_config.parameters:
            parameters.append(ParameterFactory.create(parameter))

        modality = DataModalityResolver.resolve(signature_config.data_encoding)

        model_signature = ModelSignature(
            signature_type=signature_type,
            data_modality=modality,
            data_domain=modality,
            data_encoding=signature_config.data_encoding,
            receive_format=signature_config.receive_format,
            http_location=HttpLocation.Body,
            hidden=False,
            display_title=signature_config.display_title,
            default_value=None,
            parameters=parameters
        )
        return model_signature
