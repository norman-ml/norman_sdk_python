from norman_objects.shared.models.aggregate_tag import AggregateTag
from norman_utils_external.singleton import Singleton

from norman.objects.configs.model.model_tag_config import ModelTagConfig


class AggregateTagFactory(metaclass=Singleton):

    @staticmethod
    def create(tag_config: ModelTagConfig) -> AggregateTag:
        aggregate_tag = AggregateTag(
            name=tag_config.name
        )

        return aggregate_tag
