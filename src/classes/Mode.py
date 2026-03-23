from enum import Enum


class Mode(str, Enum):
    BATCH = "batch"
    STREAMING = "streaming"
