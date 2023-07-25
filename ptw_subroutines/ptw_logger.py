import logging, sys

logger = logging.getLogger('PyTurboWizard')

def init_logger(console_output:bool = True):
    from ptw_subroutines import utilities
    loggerFileName = utilities.get_free_filename(dirname=".", base_filename='PyTurboWizard.log')
    logger.setLevel(logging.DEBUG)
    format = '%(asctime)s - {%(filename)s:%(lineno)d} - %(levelname)s - %(message)s'
    logging.basicConfig(filename=loggerFileName, encoding='utf-8', level=logging.DEBUG, format=format)
    if console_output:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
    logger.info(f"Logger initialized: {loggerFileName}")
    return logger

def getLogger():
    return logger