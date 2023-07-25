import logging, sys

def init_logger(console_output:bool = True, file_output:bool = True):
    from ptw_subroutines import utilities
    logger = getLogger()
    logger.setLevel(logging.INFO)
    if console_output:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(fmt='%(name)-12s: %(levelname)-8s - %(message)s')
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
    if file_output:
        loggerFileName = utilities.get_free_filename(dirname=".", base_filename='PyTurboWizard.log')
        handler = logging.FileHandler(filename=loggerFileName, encoding='utf-8')
        formatter = logging.Formatter(fmt='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        logger.info(f"Logger-File-Handler: {loggerFileName}")
    logger.info(f"Logger initialized")
    return logger

def getLogger():
    logger = logging.getLogger('PyTurboWizard')
    return logger