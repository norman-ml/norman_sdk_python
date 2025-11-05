from norman_objects.shared.parameters.data_modality import DataModality


class DataModalityResolver:
    _AUDIO_ENCODINGS = {"mp3", "wav"}
    _VIDEO_ENCODINGS = {"avi", "mp4"}
    _IMAGE_ENCODINGS = {"jpeg", "jpg", "png"}
    _TEXT_ENCODINGS  = {"ascii", "string", "str", "text", "txt", "utf8", "utf16"}
    _FLOAT_ENCODINGS = {"double", "f16", "f32", "f64", "float"}
    _INT_ENCODINGS   = {"int", "uint"}

    @staticmethod
    def resolve(data_encoding: str) -> DataModality:
        if not data_encoding or not isinstance(data_encoding, str):
            raise ValueError("Invalid data_encoding: must be a non-empty string")

        encoding = data_encoding.lower().strip()

        if encoding in DataModalityResolver._AUDIO_ENCODINGS:
            return DataModality.Audio

        if encoding in DataModalityResolver._VIDEO_ENCODINGS:
            return DataModality.Video

        if encoding in DataModalityResolver._IMAGE_ENCODINGS:
            return DataModality.Image

        if encoding in DataModalityResolver._TEXT_ENCODINGS:
            return DataModality.Text

        if encoding in DataModalityResolver._FLOAT_ENCODINGS:
            return DataModality.Float

        if encoding in DataModalityResolver._INT_ENCODINGS:
            return DataModality.Integer

        return DataModality.File
