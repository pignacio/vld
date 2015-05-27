#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import logging
import os

from pignacio_scripts.terminal.color import green, blue, red

from vld.constants import DATA_DIR
from vld.ingredient import IngredientMap
from vld.objects import NutritionalValue, LogData
from vld.serialization import load_ingredients
from vld.parse import parse_log_data, ParseError
from vld.utils import base_argument_parser

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def get_argument_parser():
    parser = base_argument_parser()
    parser.add_argument(
        'data',
        nargs="+",
        help=('Ingredients to count in format <ingredient>, <amount> <unit>. '
              'Multiple ingredients must be separated with "+"'))
    return parser


def main(options):
    parts = " ".join(options.data).split("+")
    ingredients = load_ingredients(os.path.join(DATA_DIR, 'ingredients'))
    ingredient_map = IngredientMap(ingredients)
    datas = [make_log_data(p, ingredient_map, n) for n, p in enumerate(parts)]

    for data in datas:
        print_log_data(data)
        print

    if len(datas) > 1:
        print_log_data(LogData.from_parts("TOTAL", datas))


def make_log_data(line, ingredient_map, part_num):
    try:
        return parse_log_data(line, ingredient_map)
    except ParseError as err:
        logging.warning("%s (Part #%s)", err, part_num + 1)
        return LogData(name=line.strip(),
                       nutritional_value=NutritionalValue.UNKNOWN)


def print_log_data(data):
    print green(data.name)
    if data.nutritional_value == NutritionalValue.UNKNOWN:
        print "  Nutritional value:", red("UNKNOWN")
    else:
        for key, value in data.nutritional_value.values().items():
            print blue("  {}:".format(key)),
            print "???" if value is None else value
