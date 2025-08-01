# Copyright (C) 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
PyTurboWizard Logger Module

This module provides logging functionality for the PyTurboWizard application.
It sets up a centralized logger to track application events, errors, and debugging information.
"""


import logging
import os

from . import misc_utils

logger = logging.getLogger("PyTurboWizard")


def init_logger(console_output: bool = True, file_output: bool = True):
    """Initialize the logger for the PyTurboWizard application."""
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        if file_output:
            pathtoFileHandler = add_filehandler()
            print(f"Logger-File-Handler: {pathtoFileHandler}")
        if console_output:
            add_streamhandler()
        logger.info("Logger initialized")
    else:
        logger.info("Logger already initialized with handlers")

    return logger


def add_streamhandler():
    """Add a stream handler to the logger to output logs to the console."""
    handler = logging.StreamHandler()
    formatter = logging.Formatter(fmt="%(name)-12s: %(levelname)-8s - %(message)s")
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.info("Logger-Stream-Handler added")


def add_filehandler():
    """Add a file handler to the logger to output logs to a file."""

    logger_file_name = misc_utils.get_free_filename_max_index(
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
    """Remove handlers from the logger."""
    for handler in logger.handlers:
        if streamhandlers and (type(handler) is logging.StreamHandler):
            logger.info("Removing StreamHandler from logger")
            logger.removeHandler(handler)
        elif filehandlers and (type(handler) is logging.FileHandler):
            logger.info("Removing FileHandler from logger")
            logger.removeHandler(handler)


def get_logger():
    """Get the logger instance."""
    return logger
