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

    parts = [process_log(f, ingredients) for f in options.file]
    parts = [p for p in parts if p]
    log = LogData.from_parts('all', parts)
    if not parts:
        print "The logs were empty :("
        return
    width = get_terminal_size()[0]
    if options.by_ingredient:
        logs = [group_by_ingredient(log, ingredients)]
    elif options.by_category:
        logs = [group_by_category(log, ingredients)]
    else:
        logs = parts

    for log in logs:
        print_log(log, max_levels=options.depth, width=width)


def get_argument_parser():
    parser = base_argument_parser()
    parser.add_argument('file', help='file/directory to process', nargs='+')
    parser.add_argument('-d', '--depth',
                        default=None,
                        type=int,
                        help="Max depth to show.")
    parser.add_argument(
        '--by-ingredient',
        action='store_true',
        default=False,
        help="Report the nutritional value grouped by ingredient.")
    parser.add_argument(
        '--by-category',
        action='store_true',
        default=False,
        help="Report the nutritional value grouped by category.")
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

    incomplete_marker = bright_red("!") if log.incomplete else " "
    unknown_marker = bright_red("*") if "???" in right_part else " "

    print(color(format_str.format(left_part, right_part)) + unknown_marker +
          incomplete_marker)

    if log.parts and (max_levels is None or level < max_levels):
        for part in log.parts:
            print_log(part, format, level + 1,
                      colors=colors,
                      max_levels=max_levels,
                      width=width)
        print


def process_log(path, ingredients):
    path = path.rstrip("/")
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
    return LogData.from_parts(os.path.basename(path), parts)


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
        return LogData(name=line.split("#", 1)[0].strip(),
                       nutritional_value=NutritionalValue.UNKNOWN,
                       incomplete=True)


def extract_leaf_log_datas(log):
    lines = []
    if not log.parts:
        lines.append(log)
    for part in log.parts:
        lines.extend(extract_leaf_log_datas(part))
    return lines


def group_by_ingredient(log, ingredients):
    leafs = extract_leaf_log_datas(log)

    grouped = collections.defaultdict(lambda: collections.defaultdict(int))
    no_ingredient = []

    for log_data in leafs:
        log_line = log_data.log_line
        if log_line and log_line.ingredient:
            grouped[log_line.ingredient.name][log_line.unit] += log_line.amount
        else:
            no_ingredient.append(log_data)

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
            log_datas.append(parts[0]._replace(ingredient=ingredient))
        else:
            name = "{} ({})".format(ingredient.name,
                                    " + ".join("{:.2f} {}".format(v, k)
                                               for k, v in amounts.items()))
            log_datas.append(LogData.from_parts(name, parts,
                                                ingredient=ingredient))

    log_datas.extend(no_ingredient)

    log_datas.sort(key=lambda x: x.nutritional_value.calories, reverse=True)

    return LogData.from_parts('By ingredient', log_datas)


def group_by_category(log, ingredients):
    by_ingredient = group_by_ingredient(log, ingredients)
    by_category = collections.defaultdict(list)

    for part in by_ingredient.parts:
        try:
            category = part.ingredient.categories[0]
        except (IndexError, AttributeError):
            category = 'unknown'

        by_category[category.strip().lower()].append(part)

    categories = [LogData.from_parts(category.capitalize(), parts)
                  for category, parts in by_category.items()]

    categories.sort(key=lambda d: d.nutritional_value.calories, reverse=True)

    return LogData.from_parts('By categories', categories)
