from norman_objects.shared.models.model_tag import ModelTag
from norman_utils_external.singleton import Singleton

from norman.managers.authentication_manager import AuthenticationManager
from norman.objects.configs.model.model_tag_config import ModelTagConfig


class TagFactory(metaclass=Singleton):
    """
    Factory responsible for constructing `ModelTag` objects based on a
    high-level `ModelTagConfig`. Tags are lightweight metadata elements used
    to categorize or annotate models in the Norman platform.

    The factory automatically injects the authenticated user's account ID
    into created tags, ensuring proper ownership metadata is preserved.

    **Methods**
    """

    authentication_manager = AuthenticationManager()

    @staticmethod
    def create(tag_config: ModelTagConfig) -> ModelTag:
        """
        Create a `ModelTag` instance from the provided configuration, assigning
        both the tag name and the ID of the authenticated user who owns it.

        **Parameters**

        - **tag_config** (`ModelTagConfig`)
            Configuration object describing the tag’s human-readable name.

        **Returns**

        - **ModelTag**
            A fully initialized tag containing the owning user's `account_id`
            and the name specified in the configuration.

        **Raises**

        - No explicit exceptions are raised by this method, but downstream
          validation may fail if the configuration contains invalid values.
        """
        model_tag = ModelTag(
            account_id=TagFactory.authentication_manager.account_id,
            name=tag_config.name
        )

        return model_tag

