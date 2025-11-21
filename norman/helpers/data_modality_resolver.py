from norman_objects.shared.parameters.data_modality import DataModality


class DataModalityResolver:
    _ENCODING_MAP = {
        # Audio
        "mp3":  DataModality.Audio,
        "wav":  DataModality.Audio,

        # Video
        "mp4":  DataModality.Video,
        "avi":  DataModality.Video,

        # Image
        "jpg":  DataModality.Image,
        "jpeg": DataModality.Image,
        "png":  DataModality.Image,

        # Text
        "txt":   DataModality.Text,

        # Numeric: float
        "double": DataModality.Float,
        "f16":    DataModality.Float,
        "f32":    DataModality.Float,
        "f64":    DataModality.Float,

        # Numeric: int
        "uint":   DataModality.Integer
    }

    @staticmethod
    def resolve(data_encoding: str) -> DataModality:
        if not isinstance(data_encoding, str) or data_encoding is None:
            raise ValueError("Invalid data_encoding: must be a non-empty string")

        encoding = data_encoding.lower().strip()

        if encoding not in DataModalityResolver._ENCODING_MAP:
            raise ValueError(f"Unknown data encoding: {data_encoding}")

        return DataModalityResolver._ENCODING_MAP[encoding]
