from norman_objects.shared.parameters.data_modality import DataModality


class SignatureModalityResolver:
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
        "mp4": DataModality.Video
    }

    @staticmethod
    def resolve(encoding: str) -> DataModality:
        if encoding is None or not isinstance(encoding, str):
            raise ValueError("encoding must be a non-empty string")

        stripped_encoding = encoding.lower().strip()
        if stripped_encoding not in SignatureModalityResolver._Encoding_Map:
            raise ValueError(f"Unknown signature encoding: {stripped_encoding}")

        return SignatureModalityResolver._Encoding_Map[stripped_encoding]
