import os
import logging

logger = logging.getLogger("PyTurboWizard")


def init_logger(console_output: bool = True, file_output: bool = True):
    logger.setLevel(logging.INFO)
    if file_output:
        pathtoFileHandler = add_filehandler()
        print(f"Logger-File-Handler: {pathtoFileHandler}")
    if console_output:
        add_streamhandler()
    logger.info(f"Logger initialized")
    return logger


def add_streamhandler():
    handler = logging.StreamHandler()
    formatter = logging.Formatter(fmt="%(name)-12s: %(levelname)-8s - %(message)s")
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.info(f"Logger-Stream-Handler added")


def add_filehandler():
    from src.subroutines.utils import misc_utils

    logger_file_name = misc_utils.get_free_filename_maxIndex(
        dirname=".", base_filename="PyTurboWizard.log"
    )
    handler = logging.FileHandler(filename=logger_file_name, encoding="utf-8")
    formatter = logging.Formatter(
        fmt="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.info(f"Logger-File-Handler added: {os.path.abspath(logger_file_name)}")
    return os.path.abspath(logger_file_name)


def remove_handlers(streamhandlers: bool = True, filehandlers: bool = True):
    # Loops over all Handlers & removes all stream- and/or file-handlers
    for handler in logger.handlers:
        if streamhandlers and (type(handler) is logging.StreamHandler):
            logger.info(f"Removing StreamHandler from logger")
            logger.removeHandler(handler)
        elif filehandlers and (type(handler) is logging.FileHandler):
            logger.info(f"Removing FileHandler from logger")
            logger.removeHandler(handler)


def getLogger():
    return logger
