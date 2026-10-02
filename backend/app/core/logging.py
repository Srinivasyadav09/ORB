import logging
import logging.config


def configure_logging(debug: bool = False) -> None:
    """Configure concise application logging without request secrets or bodies."""
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": "DEBUG" if debug else "INFO",
                }
            },
            "root": {"handlers": ["console"], "level": "DEBUG" if debug else "INFO"},
        }
    )
