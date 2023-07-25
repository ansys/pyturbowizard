import logging

logger = logging.getLogger('PyTurboWizard')

def init_logger(console_output:bool = True, file_output:bool = True):
    from ptw_subroutines.utils import utilities
    logger.setLevel(logging.INFO)
    if console_output:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(fmt='%(name)-12s: %(levelname)-8s - %(message)s')
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
    if file_output:
        logger_file_name = utilities.get_free_filename(dirname=".", base_filename='PyTurboWizard.log')
        handler = logging.FileHandler(filename=logger_file_name, encoding='utf-8')
        formatter = logging.Formatter(fmt='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        logger.info(f"Logger-File-Handler: {logger_file_name}")
    logger.info(f"Logger initialized")
    return logger

def getLogger():
    return logger