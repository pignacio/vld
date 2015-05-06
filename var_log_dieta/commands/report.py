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
from ..ingredient import IngredientMap
from ..objects import NutritionalValue, LogData
from ..parse import parse_log_data, ParseError
from ..serialization import load_ingredients
from ..utils import base_argument_parser, get_terminal_size

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

_DEFAULT_FORMAT = (
    '%(calories)s kCal (%(carbs)4s c, %(protein)4s p, %(fat)4s f) '
    '[%(fiber)4s df]')

_DEFAULT_COLORS = [bright_green, bright_blue, bright_magenta, bright_cyan, red]


def main(options):
    ingredients = IngredientMap(load_ingredients(os.path.join(DATA_DIR,
                                                              'ingredients')))

    log = process_log(options.file, ingredients)
    if log is None:
        print "The log was empty :("
        return
    width = get_terminal_size()[0]
    if options.by_ingredient:
        log = group_by_ingredient(log, ingredients)
        options.depth = None
    print_log(log, max_levels=options.depth, width=width)


def get_argument_parser():
    parser = base_argument_parser()
    parser.add_argument('file', help='file/directory to process')
    parser.add_argument('-d', '--depth',
                        default=None,
                        type=int,
                        help="Max depth to show.")
    parser.add_argument(
        '--by-ingredient',
        action='store_true',
        default=False,
        help="Report the nutritional value grouped by ingredient.")
    return parser


def _log_values(nut_value):
    return {
        f: "???" if v is None else "{:.1f}".format(v)
        for f, v in nut_value._asdict().items()
    }


# pylint: disable=too-many-arguments,redefined-builtin
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
            init_parts = init.parts if init else []
        else:
            init_parts = []

        parts = [process_log(os.path.join(path, p), ingredients)
                 for p in log_parts]
        parts.extend(init_parts)

    parts = [p for p in parts if p]

    if not parts:
        return None
    return LogData(name=os.path.basename(path),
                   nutritional_value=NutritionalValue.sum(p.nutritional_value
                                                          for p in parts),
                   parts=parts)


def get_log_file_parts(path, ingredients):
    with open(path) as fin:
        lines = (l for l in fin if l.strip() and not l.strip().startswith('#'))

        return [make_log_data(l, ingredients, path, ln)
                for ln, l in enumerate(lines)]


def make_log_data(line, ingredients, path, line_num):
    try:
        return parse_log_data(line, ingredients)
    except ParseError as err:
        logging.warning("%s (%s:%s)", err, path, line_num)
        return LogData(name=line.strip(),
                       nutritional_value=NutritionalValue.UNKNOWN)


def extract_log_lines(log):
    lines = []
    if log.log_line is not None:
        lines.append(log.log_line)
    for part in log.parts:
        lines.extend(extract_log_lines(part))
    return lines


def group_by_ingredient(log, ingredients):
    log_lines = extract_log_lines(log)

    grouped = collections.defaultdict(lambda: collections.defaultdict(int))

    for log_line in log_lines:
        if log_line.ingredient is not None:
            grouped[log_line.ingredient.name][log_line.unit] += log_line.amount

    log_datas = []

    for ingredient_name, amounts in grouped.items():
        ingredient = ingredients[ingredient_name]
        parts = []
        for unit, amount in amounts.items():
            try:
                nut_value = ingredient.get_nutritional_value(amount, unit)
            except CantConvert as err:
                logger.warning(str(err))
                nut_value = NutritionalValue.UNKNOWN
            parts.append(LogData(
                name="{} ({} {})".format(ingredient.name, amount, unit),
                nutritional_value=nut_value))
        parts.sort(key=lambda x: x.nutritional_value.calories, reverse=True)

        if len(parts) == 1:
            log_datas.append(parts[0])
        else:
            name = "{} ({})".format(ingredient.name,
                                    " + ".join("{:.2f} {}".format(v, k)
                                               for k, v in amounts.items()))
            log_datas.append(LogData(name=name,
                                     parts=parts,
                                     nutritional_value=NutritionalValue.sum(
                                         p.nutritional_value for p in parts)))

    log_datas.sort(key=lambda x: x.nutritional_value.calories, reverse=True)

    return LogData(name='By ingredient',
                   nutritional_value=NutritionalValue.sum(ld.nutritional_value
                                                          for ld in log_datas),
                   parts=log_datas)
