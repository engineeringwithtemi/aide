import structlog
import logging
import sys
from pathlib import Path


def setup_logging(
    log_level: str = "INFO",
    log_to_file: bool = False,
    log_file_path: str = "logs/app.log",
    json_format: bool = True,
):
    if log_to_file:
        Path(log_file_path).parent.mkdir(parents=True, exist_ok=True)

    if json_format:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.CallsiteParameterAdder(  # Adds file, function, line number
            [
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if log_to_file:
        structlog.configure(
            processors=shared_processors
            + [
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        formatter = structlog.stdlib.ProcessorFormatter(
            processor=renderer,
            foreign_pre_chain=shared_processors,
        )

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)

        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.handlers = []
        root_logger.addHandler(stdout_handler)
        root_logger.addHandler(file_handler)
        root_logger.setLevel(log_level)
    else:
        structlog.configure(
            processors=shared_processors + [renderer],
            wrapper_class=structlog.make_filtering_bound_logger(
                logging.getLevelName(log_level)
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(sys.stdout),
            cache_logger_on_first_use=True,
        )


def get_logger(name: str | None = None) -> structlog.typing.FilteringBoundLogger:
    return structlog.get_logger(name)
