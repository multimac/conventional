import io
import os


def create_pipe_streams(additional_mode: str = ""):
    read, write = os.pipe()

    read_stream = os.fdopen(read, "r" + additional_mode)
    write_steam = os.fdopen(write, "w" + additional_mode)

    return read_stream, write_steam
