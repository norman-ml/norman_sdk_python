from norman_objects.shared.model_signatures.signature_type import SignatureType
from norman_objects.shared.models.http_request_type import HttpRequestType
from norman_objects.shared.models.model import Model
from norman_objects.shared.models.model_hosting_location import ModelHostingLocation
from norman_objects.shared.models.model_type import ModelType
from norman_objects.shared.models.output_format import OutputFormat
from norman_utils_external.singleton import Singleton

from norman.managers.authentication_manager import AuthenticationManager
from norman.objects.configs.model.model_config import ModelConfig
from norman.objects.factories.asset_factory import AssetFactory
from norman.objects.factories.signature_factory import SignatureFactory
from norman.objects.factories.tag_factory import TagFactory


class ModelFactory(metaclass=Singleton):
    authentication_manager = AuthenticationManager()

    @staticmethod
    def create(model_config: ModelConfig) -> Model:
        model_class = model_config.model_class
        if model_config.model_class is None:
            model_class = ""

        request_type = model_config.request_type
        if request_type is None:
            request_type = HttpRequestType.Post

        model_type = model_config.model_type
        if model_config.model_type is None:
            model_type = ModelType.Pytorch_jit

        output_format = model_config.output_format
        if output_format is None:
            output_format = OutputFormat.Json

        hosting_location = model_config.hosting_location
        if hosting_location is None:
            hosting_location = ModelHostingLocation.Internal

        if hosting_location == ModelHostingLocation.External:
            if model_config.url is None:
                raise ValueError("External models must define a url field in ModelConfig")
            url = model_config.url
        else:
            url = ""

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

        http_headers = {}
        if model_config.http_headers is not None:
            http_headers = model_config.http_headers

        user_added_tags = []
        if model_config.user_added_tags is not None:
            for tag_config in model_config.user_added_tags:
                created = TagFactory.create(tag_config)
                user_added_tags.append(created)

        model = Model(
            account_id=ModelFactory.authentication_manager.account_id,
            version_label=model_config.version_label,
            active=True,
            name=model_config.name,
            model_class=model_class,
            url=url,
            request_type=request_type,
            model_type=model_type,
            hosting_location=hosting_location,
            output_format=output_format,
            short_description=model_config.short_description,
            long_description=model_config.long_description,
            inputs=inputs,
            outputs=outputs,
            http_headers=http_headers,
            assets=assets,
            user_added_tags=user_added_tags
        )

        return model
