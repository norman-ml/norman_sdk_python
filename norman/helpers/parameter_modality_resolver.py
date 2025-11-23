from norman_objects.shared.parameters.data_modality import DataModality


class ParameterModalityResolver:
    _ENCODING_MAP = {
        # Text encodings
        "utf-8":  DataModality.Text,
        "utf-16": DataModality.Text,

        # Raw audio encodings
        "pcm":      DataModality.Audio,
        "wav-pcm":  DataModality.Audio,

        # Video frame encodings (raw streams)
        "yuv420p": DataModality.Video,
        "x264":    DataModality.Video,
        "h264":    DataModality.Video,
        "h265":    DataModality.Video,

        # Numeric encodings
        "float16": DataModality.Float,
        "float32": DataModality.Float,
        "float64": DataModality.Float,

        "uint": DataModality.Integer
    }

    @staticmethod
    def resolve(encoding: str) -> DataModality:
        if not encoding or not isinstance(encoding, str):
            raise ValueError("encoding must be a non-empty string")

        encoding = encoding.lower().strip()

        if encoding not in ParameterModalityResolver._ENCODING_MAP:
            raise ValueError(f"Unknown parameter encoding: {encoding}")

        return ParameterModalityResolver._ENCODING_MAP[encoding]
