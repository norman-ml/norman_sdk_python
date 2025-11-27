from norman_objects.shared.parameters.data_modality import DataModality


class SignatureModalityResolver:
    _ENCODING_MAP = {
        # Image
        "jpg":  DataModality.Image,
        "jpeg": DataModality.Image,
        "png":  DataModality.Image,

        # Audio (container level)
        "mp3": DataModality.Audio,
        "wav": DataModality.Audio,

        # Video (container level)
        "mp4": DataModality.Video,
        "avi": DataModality.Video,

        # Text
        "txt":   DataModality.Text
    }

    @staticmethod
    def resolve(encoding: str) -> DataModality:
        if not encoding or not isinstance(encoding, str):
            raise ValueError("encoding must be a non-empty string")

        encoding = encoding.lower().strip()

        if encoding not in SignatureModalityResolver._ENCODING_MAP:
            raise ValueError(f"Unknown signature encoding: {encoding}")

        return SignatureModalityResolver._ENCODING_MAP[encoding]
