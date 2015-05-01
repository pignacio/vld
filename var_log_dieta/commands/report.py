# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import collections
import logging
import os

from pignacio_scripts.terminal.color import (bright_blue, bright_cyan,
                                             bright_green, bright_magenta,
                                             bright_red, red)

from ..constants import DATA_DIR
from ..conversions import CantConvert
from ..objects import NutritionalValue
from ..serialization import load_ingredients
from ..utils import base_argument_parser, get_terminal_size

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

LogData = collections.namedtuple('LogData', ['name', 'nutritional_value',
                                             'parts'])

_DEFAULT_FORMAT = (
    '%(calories)s kCal (%(carbs)4s c, %(protein)4s p, %(fat)4s f) '
    '[%(fiber)4s df]')

_DEFAULT_COLORS = [bright_green, bright_blue, bright_magenta, bright_cyan, red]


def main(options):
    ingredients = {
        i.name.lower(): i
        for i in load_ingredients(os.path.join(DATA_DIR, 'ingredients'))
    }

    log = process_log(options.file, ingredients)
    width = get_terminal_size()[0]
    print_log(log, max_levels=options.depth, width=width)


def get_argument_parser():
    parser = base_argument_parser()
    parser.add_argument('file', help='file/directory to process')
    parser.add_argument('-d', '--depth',
                        default=None,
                        type=int,
                        help="Max depth to show")
    return parser


def _log_values(nut_value):
    return {
        f: "???" if v is None else "{:.1f}".format(v)
        for f, v in nut_value._asdict().items()
    }


def print_log(log,
              format=_DEFAULT_FORMAT,
              level=0,
              width=100,
              colors=None,
              max_levels=None):
    colors = colors or _DEFAULT_COLORS
    right_part = format % _log_values(log.nutritional_value)
    left_part = '{}{}:'.format(' ' * level, log.name)
    right_size = max(0, width - len(left_part) - 2)
    format_str = '{}{:>' + str(right_size) + '}'

    try:
        color = colors[level]
    except IndexError:
        color = lambda s: s

    unknown_marker = bright_red(" *") if "???" in right_part else ""

    print color(format_str.format(left_part, right_part)) + unknown_marker

    if log.parts and (max_levels is None or level < max_levels):
        for part in log.parts:
            print_log(part, format, level + 1,
                      colors=colors,
                      max_levels=max_levels,
                      width=width)
        print


def process_log(path, ingredients):
    if os.path.isfile(path):
        parts = get_log_file_parts(path, ingredients)
    else:
        log_parts = sorted(os.listdir(path))

        if '__init__' in log_parts:
            log_parts.remove('__init__')
            init = process_log(os.path.join(path, '__init__'), ingredients)
            init_parts = init.parts
        else:
            init_parts = []

        parts = [process_log(os.path.join(path, p), ingredients)
                 for p in log_parts]
        parts.extend(init_parts)

    return LogData(name=os.path.basename(path),
                   nutritional_value=NutritionalValue.sum(p.nutritional_value
                                                          for p in parts),
                   parts=parts)


def get_log_file_parts(path, ingredients):
    parts = []
    with open(path) as fin:
        lines = fin.readlines()

    lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]

    for line_num, line in enumerate(lines):
        line = line.rstrip()
        name, quantity = line.split(',', 1)
        amount, unit = quantity.split(None, 1)

        try:
            ingredient = ingredients[name.lower()]
        except KeyError:
            logging.warning('Invalid ingredient: "%s" (%s:%s)', name, path,
                            line_num)
            ingredient = None

        nutritional_value = _get_line_nutritional_value(path, line_num, amount,
                                                        unit, ingredient)
        data_name = name if ingredient is None else ingredient.name
        parts.append(LogData(name='{}, {} {}'.format(data_name, amount, unit),
                             nutritional_value=nutritional_value,
                             parts=[]))

    return parts


def _get_line_nutritional_value(path, line_num, amount, unit, ingredient):
    if ingredient is None:
        return NutritionalValue.UNKNOWN

    try:
        amount = float(amount)
    except ValueError:
        logging.warning('Invalid amount: "%s" (%s:%s)', amount, path, line_num)
        return NutritionalValue.UNKNOWN

    try:
        return ingredient.get_nutritional_value(amount, unit)
    except CantConvert as err:
        logging.warning(str(err) + " ({}:{})".format(path, line_num))
        return NutritionalValue.UNKNOWN
