import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_FILE = LOG_DIR / "app.log"
_file_handler: RotatingFileHandler | None = None
_console_handler: logging.StreamHandler | None = None


def _get_file_handler() -> RotatingFileHandler:
	global _file_handler
	if _file_handler is None:
		LOG_DIR.mkdir(parents=True, exist_ok=True)
		_file_handler = RotatingFileHandler(
			LOG_FILE,
			maxBytes=10 * 1024 * 1024,
			backupCount=2,
			encoding="utf-8",
		)
		_file_handler.setFormatter(_formatter())
	return _file_handler


def _get_console_handler() -> logging.StreamHandler:
	global _console_handler
	if _console_handler is None:
		_console_handler = logging.StreamHandler()
		_console_handler.setFormatter(_formatter())
	return _console_handler


def _formatter() -> logging.Formatter:
	return logging.Formatter(
		"%(asctime)s | %(levelname)s | %(name)s | %(message)s",
		datefmt="%Y-%m-%d %H:%M:%S",
	)


def setup_logger(name: str = "macrotracker", level: int = logging.INFO) -> logging.Logger:
	logger = logging.getLogger(name)
	logger.setLevel(level)
	logger.propagate = False

	for handler in (_get_file_handler(), _get_console_handler()):
		if handler not in logger.handlers:
			logger.addHandler(handler)

	return logger
