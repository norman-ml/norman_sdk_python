from norman_objects.shared.parameters.data_modality import DataModality


class ParameterModalityResolver:
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
        "utf8": DataModality.Text,
        "utf16": DataModality.Text,

        # Video frame encodings (raw streams)
        "h264": DataModality.Video,
        "h265": DataModality.Video,
        "rgb24": DataModality.Video,
        "x264": DataModality.Video,
        "yuv420p": DataModality.Video
    }

    @staticmethod
    def resolve(encoding: str) -> DataModality:
        if encoding is None or not isinstance(encoding, str):
            raise ValueError("encoding must be a non-empty string")

        stripped_encoding = encoding.lower().strip()
        if stripped_encoding not in ParameterModalityResolver._Encoding_Map:
            raise ValueError(f"Unknown parameter encoding: {stripped_encoding}")

        return ParameterModalityResolver._Encoding_Map[stripped_encoding]
