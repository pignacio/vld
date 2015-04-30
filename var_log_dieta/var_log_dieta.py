# -*- coding: utf-8 -*-
import collections
import logging
import os
import sys

from pignacio_scripts.terminal.color import (bright_green, bright_blue,
                                             bright_magenta, bright_cyan,
                                             bright_red, red)

from .constants import DATA_DIR
from .conversions import CantConvert
from .objects import NutritionalValue
from .serialization import load_ingredients


def main():
    logging.basicConfig(stream=sys.stdout,
                        level=logging.DEBUG,
                        format='%(asctime)s %(levelname)6s %(message)s')
    ingredients = {
        i.name.lower(): i
        for i in load_ingredients(os.path.join(DATA_DIR, 'ingredients'))
    }

    log = process_log(sys.argv[1], ingredients)
    print
    print_log(log)


LogData = collections.namedtuple('LogData', ['name', 'nutritional_value',
                                             'parts'])

_DEFAULT_FORMAT = (
    '%(calories)s kCal (%(carbs)4s c, %(protein)4s p, %(fat)4s f) '
    '[%(fiber)4s]')

_DEFAULT_COLORS = [bright_green, bright_blue, bright_magenta, bright_cyan,
                   red]


def _log_values(nut_value):
    return {
        f: "???" if v is None else "{:.1f}".format(v)
        for f, v in nut_value._asdict().items()
    }


def print_log(log,
              format=_DEFAULT_FORMAT,
              level=0,
              width=100,
              colors=_DEFAULT_COLORS,
              max_levels=None):
    if max_levels is not None and level >= max_levels:
        return
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

    if log.parts:
        # print
        for part in log.parts:
            print_log(part, format, level + 1,
                      colors=colors,
                      max_levels=max_levels)
        print


def process_log(path, ingredients):
    if os.path.isfile(path):
        parts = get_log_file_parts(path, ingredients)
    else:
        log_parts = sorted(os.listdir(path))

        parts = []
        if '__init__' in log_parts:
            log_parts.remove('__init__')
            init = process_log(os.path.join(path, '__init__'), ingredients)
            parts = init.parts

        parts.extend([process_log(os.path.join(path, p), ingredients)
                      for p in log_parts])

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

        parts.append(LogData(name='{}, {} {}'.format(
            name if ingredient is None else ingredient.name, amount, unit),
                             nutritional_value=_get_line_nutritional_value(
                                 path, line_num, amount, unit, ingredient),
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
        logging.warning(str(err))
        return NutritionalValue.UNKNOWN
