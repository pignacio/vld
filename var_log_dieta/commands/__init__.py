#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import logging
import sys

from ..utils import base_argument_parser
from . import report, new_ingredient, count, show_ingredients, price

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def run_command(command_func, argument_parser=None):
    argument_parser = argument_parser or base_argument_parser()

    options = argument_parser.parse_args()

    if options.verbosity:
        level = logging.DEBUG if options.verbosity > 1 else logging.INFO
        logging.basicConfig(stream=sys.stdout,
                            level=level,
                            format='%(asctime)s %(levelname)7s %(message)s')

    return command_func(options)


def vld_report():
    return run_command(report.main, report.get_argument_parser())


def vld_new_ingredient():
    return run_command(new_ingredient.main,
                       new_ingredient.get_argument_parser())


def vld_count():
    return run_command(count.main, count.get_argument_parser())


def vld_show_ingredients():
    return run_command(show_ingredients.main,
                       show_ingredients.get_argument_parser())


def vld_price():
    return run_command(price.main, price.get_argument_parser())
