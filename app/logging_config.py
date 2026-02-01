import logging
from logging.handlers import RotatingFileHandler


logger = logging.getLogger("subscription_service")
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler(
    "logs/subscription_service.log",
    maxBytes=10_000_000,
    backupCount=5,
)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
