import logging
from typing import Dict, TypedDict

import typer


class ColourConfig(TypedDict):
    fg: str


class ColorFormatter(logging.Formatter):
    colours: Dict[str, ColourConfig] = {
        "error": dict(fg="red"),
        "exception": dict(fg="red"),
        "critical": dict(fg="red"),
        "debug": dict(fg="blue"),
        "warning": dict(fg="yellow"),
    }

    def format(self, record: logging.LogRecord) -> str:
        if not record.exc_info:
            level = record.levelname.lower()
            msg = record.getMessage()

            if level in self.colours:
                prefix = typer.style("{}: ".format(level), **self.colours[level])
                msg = "\n".join(prefix + x for x in msg.splitlines())

            return msg
        return logging.Formatter.format(self, record)


class TyperHandler(logging.Handler):
    _use_stderr = True

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            typer.echo(msg, err=self._use_stderr)
        except Exception:
            self.handleError(record)
