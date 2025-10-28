import re
from norman_objects.shared.parameters.data_modality import DataModality


class DataModalityResolver:
    @staticmethod
    def resolve(data_encoding: str) -> DataModality:
        if not data_encoding or not isinstance(data_encoding, str):
            raise ValueError("Invalid data_encoding: must be a non-empty string")

        encoding = data_encoding.lower().strip()

        # ---- Audio ----
        if re.search(r"(mp3|wav|flac|ogg|m4a)", encoding):
            return DataModality.Audio

        # ---- Video ----
        if re.search(r"(mp4|avi|mov|mkv|webm)", encoding):
            return DataModality.Video

        # ---- Image ----
        if re.search(r"(jpg|jpeg|png|bmp|gif|tiff|webp)", encoding):
            return DataModality.Image

        # ---- Text ----
        if re.search(r"(utf|ascii|text|txt|str|string)", encoding):
            return DataModality.Text

        # ---- Float ----
        if re.search(r"(float|f16|f32|f64|double)", encoding):
            return DataModality.Float

        # ---- Integer ----
        if re.search(r"(int|i8|i16|i32|i64|uint)", encoding):
            return DataModality.Integer

        # ---- Fallback: File ----
        return DataModality.File
