from norman_objects.shared.parameters.data_modality import DataModality


class ParameterModalityResolver:
    """
    Utility class for determining the high-level `DataModality` associated with
    a parameter’s declared encoding. This resolver maps common encoding names
    (e.g., `"mp3"`, `"png"`, `"utf-8"`) to modality categories such as
    `Audio`, `Image`, `Text`, and `Video`.

    The resolver is used within the Norman SDK to validate parameter metadata
    and decide how inputs should be interpreted or transformed before being
    sent to a model.

    **Methods**
    """

    _Encoding_Map = {
        # Audio (frame level)
        "aac": DataModality.Audio,
        "mp3": DataModality.Audio,
        "wav": DataModality.Audio,

        # Image
        "jpg": DataModality.Image,
        "jpeg": DataModality.Image,
        "png": DataModality.Image,

        # Text encodings
        "utf-8": DataModality.Text,
        "utf-16": DataModality.Text,

        # Video frame encodings (raw streams)
        "h264": DataModality.Video,
        "h265": DataModality.Video,
        "libx264": DataModality.Video,
        "rgb24": DataModality.Video,
        "x264": DataModality.Video,
        "yuv420p": DataModality.Video,
    }

    @staticmethod
    def resolve(encoding: str) -> DataModality:
        """
        Resolve the given encoding string into its corresponding `DataModality`.

        The lookup is case-insensitive and trims leading/trailing whitespace.
        If the encoding is not part of the predefined `_Encoding_Map`, the
        resolver raises an error.

        **Parameters**

        - **encoding** (`str`)
            A non-empty encoding string such as `"mp3"`, `"png"`, `"utf-8"`,
            or `"h264"`. The value is normalized to lowercase before lookup.

        **Returns**

        - **DataModality**
            The modality associated with the provided encoding, such as
            `DataModality.Audio`, `DataModality.Image`, etc.

        **Raises**

        - **ValueError**
            Raised if:
            - The encoding is `None`
            - The encoding is not a string
            - The encoding is not recognized or supported
        """
        if encoding is None or not isinstance(encoding, str):
            raise ValueError("encoding must be a non-empty string")

        stripped_encoding = encoding.lower().strip()
        if stripped_encoding not in ParameterModalityResolver._Encoding_Map:
            raise ValueError(f"Unknown parameter encoding: {stripped_encoding}")

        return ParameterModalityResolver._Encoding_Map[stripped_encoding]
