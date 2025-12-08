from norman_objects.shared.parameters.data_modality import DataModality


class SignatureModalityResolver:
    """
    Utility class for resolving a model signature's declared encoding into a
    corresponding high-level `DataModality`.

    This resolver operates at the *container* level, meaning that encodings such
    as `"mp4"`, `"avi"`, `"mp3"`, or `"png"` indicate the broader data type being
    represented, rather than low-level frame encodings. The mapping determines
    how signature parameters should be interpreted when constructing invocation
    requests.

    **Methods**
    """

    _Encoding_Map = {
        # Audio (container level)
        "aac": DataModality.Audio,
        "mp3": DataModality.Audio,
        "wav": DataModality.Audio,

        # Image
        "jpg": DataModality.Image,
        "jpeg": DataModality.Image,
        "png": DataModality.Image,

        # Text
        "txt": DataModality.Text,
        "utf-8": DataModality.Text,
        "utf-16": DataModality.Text,

        # Video (container level)
        "avi": DataModality.Video,
        "mp4": DataModality.Video,
    }

    @staticmethod
    def resolve(encoding: str) -> DataModality:
        """
        Resolve a signature parameter encoding string into its corresponding
        `DataModality`.

        Encodings are matched case-insensitively and may include container-level
        formats such as `"mp4"` or `"avi"` for video, `"wav"` for audio, or
        `"txt"` for text.

        **Parameters**

        - **encoding** (`str`)
            A non-empty encoding identifier (e.g., `"mp4"`, `"png"`, `"utf-8"`).
            The value is lowercased and stripped before lookup.

        **Returns**

        - **DataModality**
            The identified modality associated with the encoding, such as
            `DataModality.Audio`, `DataModality.Image`, or `DataModality.Video`.

        **Raises**

        - **ValueError**
            Raised if:
            - The encoding is `None`
            - The encoding is not a string
            - The encoding is not recognized in the modality mapping
        """
        if encoding is None or not isinstance(encoding, str):
            raise ValueError("encoding must be a non-empty string")

        stripped_encoding = encoding.lower().strip()
        if stripped_encoding not in SignatureModalityResolver._Encoding_Map:
            raise ValueError(f"Unknown signature encoding: {stripped_encoding}")

        return SignatureModalityResolver._Encoding_Map[stripped_encoding]
