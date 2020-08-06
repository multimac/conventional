from pathlib import Path

from confuse import ConfigView, Template


class Filename(Template):
    def value(self, view: ConfigView, template: Template = None) -> Path:
        path, source = view.first()

        if not isinstance(path, str):
            self.fail(f"must be a filename, not {type(path).__name__}", view, True)

        filename = Path(path)

        if filename.is_absolute():
            return filename

        if not source.filename:
            self.fail(
                f"cannot load relative path, {filename}, from non-file config", view
            )

        return Path(source.filename).joinpath(filename)
