import logging

FORMAT = "%(levelname)s: %(message)s"


def setup_logging(level: str):
    try:
        logging.basicConfig(format=FORMAT, level=level)
    except ValueError as e:
        logging.basicConfig(format=FORMAT, level="INFO")
        logging.warning(e)
