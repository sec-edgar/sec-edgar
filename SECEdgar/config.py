# -*- coding:utf-8 -*-
__all__ = [
    'DEFAULT_DATA_PATH',
    'DEFAULT_CREDENTIALS_FILE'
]

import re
import sys
import logging
import os
from os.path import join as pjoin, expanduser

DEFAULT_CREDENTIALS_FILE = 'default.cfg'

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

cfg = configparser.ConfigParser()
cfg.read(DEFAULT_CREDENTIALS_FILE)
DEFAULT_DATA_PATH = pjoin(expanduser('~'), cfg['Paths']['data'])
