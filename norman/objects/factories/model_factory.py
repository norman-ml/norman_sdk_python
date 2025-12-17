from norman_objects.shared.model_signatures.signature_type import SignatureType
from norman_objects.shared.models.http_request_type import HttpRequestType
from norman_objects.shared.models.model_hosting_location import ModelHostingLocation
from norman_objects.shared.models.model_projection import ModelProjection
from norman_objects.shared.models.model_type import ModelType
from norman_objects.shared.models.model_version import ModelVersion
from norman_objects.shared.models.output_format import OutputFormat
from norman_utils_external.singleton import Singleton

from norman.managers.authentication_manager import AuthenticationManager
from norman.objects.configs.model.model_projection_config import ModelProjectionConfig
from norman.objects.factories.asset_factory import AssetFactory
from norman.objects.factories.signature_factory import SignatureFactory
from norman.objects.factories.tag_factory import TagFactory


class ModelFactory(metaclass=Singleton):
    authentication_manager = AuthenticationManager()

    @staticmethod
    def create(model_config: ModelProjectionConfig) -> ModelProjection:
        version_config = model_config.version
        category = version_config.category
        if category is None:
            category = ""

        request_type = version_config.request_type
        if request_type is None:
            request_type = HttpRequestType.Post

        model_type = version_config.model_type
        if model_type is None:
            model_type = ModelType.Pytorch_jit

        output_format = version_config.output_format
        if output_format is None:
            output_format = OutputFormat.Json

        hosting_location = version_config.hosting_location
        if hosting_location is None:
            hosting_location = ModelHostingLocation.Internal

        if hosting_location == ModelHostingLocation.External:
            if version_config.url is None:
                raise ValueError("External models must define a url field in ModelProjectionConfig")
            url = model_config.url
        else:
            url = ""

        inputs = []
        for signature in version_config.inputs:
            created = SignatureFactory.create(signature, SignatureType.Input)
            inputs.append(created)

        outputs = []
        for signature in version_config.outputs:
            created = SignatureFactory.create(signature, SignatureType.Output)
            outputs.append(created)

        assets = []
        for asset_config in version_config.assets:
            created = AssetFactory.create(asset_config)
            assets.append(created)

        http_headers = {}
        if version_config.http_headers is not None:
            http_headers.update(version_config.http_headers)

        user_tags = []
        if model_config.user_tags is not None:
            for tag_config in model_config.user_tags:
                created = TagFactory.create(tag_config)
                user_tags.append(created)


        model_version = ModelVersion(
            active=True,
            label=model_config.version_label,
            short_description=model_config.short_description,
            long_description=model_config.long_description,
            hosting_location=hosting_location,
            model_type=model_type,
            request_type=request_type,
            url=url,
            output_format=output_format,
            assets=assets,
            inputs=inputs,
            outputs=outputs,
            http_headers=http_headers,
        )

        model = ModelProjection(
            account_id=ModelFactory.authentication_manager.account_id,
            name=model_config.name,
            category=category,
            version=model_version,
            user_tags=user_tags
        )

        return model
