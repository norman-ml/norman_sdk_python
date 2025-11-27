from typing import Any

from norman_objects.shared.model_signatures.signature_type import SignatureType
from norman_objects.shared.models.model import Model
from norman_utils_external.singleton import Singleton

from norman.managers.authentication_manager import AuthenticationManager
from norman.objects.configs.model.model_config import ModelConfig
from norman.objects.factories.asset_factory import AssetFactory
from norman.objects.factories.signature_factory import SignatureFactory
from norman_objects.shared.models.output_format import OutputFormat
from norman_objects.shared.models.model_type import ModelType
from norman_objects.shared.models.http_request_type import HttpRequestType
from norman_objects.shared.models.model_hosting_location import ModelHostingLocation


class ModelFactory(metaclass=Singleton):

    @staticmethod
    def create(model_config: ModelConfig) -> Model:
        if model_config.model_class is None:
            model_class = ""
        else:
            model_class = model_config.model_class

        hosting_location = model_config.hosting_location
        if hosting_location is None:
            hosting_location = ModelHostingLocation.Internal

        if hosting_location == ModelHostingLocation.External:
            if model_config.url is None:
                raise ValueError("External models must define a 'url' field in ModelConfig.")
            url = model_config.url
        else:
            url = ""

        request_type = model_config.request_type
        if request_type is None:
            request_type = HttpRequestType.Post

        output_format = model_config.output_format
        if output_format is None:
            output_format = OutputFormat.Json

        model_type = model_config.model_type
        if model_config.model_type is None:
            model_type = ModelType.Pytorch_jit

        inputs = []
        for signature in model_config.inputs:
            created = SignatureFactory.create(signature, SignatureType.Input)
            inputs.append(created)

        outputs = []
        for signature in model_config.outputs:
            created = SignatureFactory.create(signature, SignatureType.Output)
            outputs.append(created)

        assets = []
        for asset_config in model_config.assets:
            created = AssetFactory.create(asset_config)
            assets.append(created)

        model = Model(
            name=model_config.name,
            model_class=model_class,
            url=url,
            request_type=request_type,
            model_type=model_type,
            hosting_location=hosting_location,
            output_format=output_format,
            long_description=model_config.long_description,
            account_id=AuthenticationManager().account_id,
            version_label=model_config.version_label,
            active=True,
            short_description=model_config.short_description,
            inputs=inputs,
            outputs=outputs,
            assets=assets
        )

        return model
