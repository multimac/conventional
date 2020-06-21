from pathlib import Path

from confuse import Template


class Filename(Template):
    def __init__(self):
        super().__init__()

    def value(self, view, template=None):
        path, source = view.first()

        if not isinstance(path, str):
            self.fail(f"must be a filename, not {type(path).__name__}", view, True)

        filename = Path(path)

        if filename.is_absolute():
            return filename

        if not source.filename:
            self.fail(f"cannot load relative path, {filename}, from non-file config", view)

        return Path(source.filename).joinpath(filename)
