from norman_objects.shared.models.model_asset import ModelAsset
from norman_utils_external.singleton import Singleton

from norman.managers.authentication_manager import AuthenticationManager
from norman.objects.configs.model.asset_config import AssetConfig


class AssetFactory(metaclass=Singleton):
    """
    Factory class responsible for constructing `ModelAsset` objects based on
    high-level `AssetConfig` definitions. This utility centralizes the logic
    for assigning authentication-derived metadata (such as `account_id`) when
    creating assets for the Norman model registry.

    The factory uses the global `AuthenticationManager` to retrieve the active
    account ID at creation time, ensuring that assets are always associated
    with the correct authenticated user.

    **Methods**
    """

    authentication_manager = AuthenticationManager()

    @staticmethod
    def create(asset_config: AssetConfig) -> ModelAsset:
        """
        Create a new `ModelAsset` instance using the provided configuration and
        the current authenticated user's account context.

        The method injects authenticated metadata (currently, `account_id`)
        into the constructed `ModelAsset`, ensuring consistency between model
        assets and the user that owns them.

        **Parameters**

        - **asset_config** (`AssetConfig`)
            Configuration object containing asset properties such as
            `asset_name`, `description`, or any additional metadata required
            for registration.

        **Returns**

        - **ModelAsset**
            A fully initialized model asset populated with the current user's
            account ID and the properties defined in `asset_config`.
        """
        asset = ModelAsset(
            account_id=AssetFactory.authentication_manager.account_id,
            asset_name=asset_config.asset_name
        )

        return asset

