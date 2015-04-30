#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import logging

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

DATA_DIR = 'data'

DEFAULT_CONVERSIONS = {
    'kg': {'g': 1000},
    'l': {'ml': 1000},
}  # yapf: disable
