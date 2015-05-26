#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import datetime
import json
import logging
import re
import os

from var_log_dieta.constants import DATA_DIR
from var_log_dieta.ingredient import IngredientMap
from var_log_dieta.serialization import load_ingredients
from var_log_dieta.parse import parse_log_data, ParseError
from var_log_dieta.objects import CantConvert, LogData, NutritionalValue
from var_log_dieta.utils import base_argument_parser

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def get_argument_parser():
    parser = base_argument_parser()
    parser.add_argument(
        'data',
        nargs='+',
        help=('Ingredients to count in format <ingredient>, <amount> <unit>. '
              'Multiple ingredients must be separated with "+"'))
    return parser


def main(options):
    parts = ' '.join(options.data).split('+')
    ingredients = load_ingredients(os.path.join(DATA_DIR, 'ingredients'))
    ingredient_map = IngredientMap(ingredients)
    _update_stock(STOCK_DIR, STOCK_CACHE_DIR, ingredient_map)
    with open(os.path.join(STOCK_CACHE_DIR,
                           datetime.date.today().strftime('%F'))) as fin:
        prices = json.load(fin)

    datas = [make_log_data(p, ingredient_map, n) for n, p in enumerate(parts)]

    total = 0
    for data in datas:
        print data.name,
        log_line = data.log_line
        if log_line and log_line.ingredient:
            ingredient = log_line.ingredient
            price = prices[ingredient.name] * ingredient.convert(
                log_line.amount, log_line.unit, ingredient.sample_unit)
            print "  $", price
            total += price
        else:
            print "BAD LINE"
        print
    print "TOTAL: $", total


def make_log_data(line, ingredient_map, part_num):
    try:
        return parse_log_data(line, ingredient_map)
    except ParseError as err:
        logging.warning("%s (Part #%s)", err, part_num + 1)
        return LogData(name=line.strip(),
                       nutritional_value=NutritionalValue.UNKNOWN)


STOCK_DIR = 'data/stock'
STOCK_CACHE_DIR = '/tmp/stock'


def _update_stock(stock_dir, cache_dir, ingredients):
    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir)
    stock_files = os.listdir(stock_dir)
    if not stock_files:
        logger.info('No stock files to process')

    start = datetime.datetime.strptime(sorted(stock_files)[0],
                                       '%Y-%m-%d').date()
    end = datetime.date.today()

    date = start
    values = {}

    while date <= end:
        date_str = date.strftime('%Y-%m-%d')
        stock_file = os.path.join(stock_dir, date_str)
        if os.path.isfile(stock_file):
            values.update(_get_price_values(stock_file, ingredients))
        with open(os.path.join(cache_dir, date_str), 'w') as fout:
            json.dump(values, fout, indent=1, sort_keys=True)
        date += datetime.timedelta(days=1)


def _get_price_values(filename, ingredients):
    prices = {}
    with open(filename) as fin:
        for line in fin:
            line = line.strip()
            logger.debug("Getting prices from line: '%s'", line)
            if not line or line.startswith('#'):
                continue
            if ':' not in line:
                continue
            log_line, data = line.split(':', 1)
            if re.match('[+-]', log_line):
                log_line = log_line[1:]

            try:
                parsed = parse_log_data(log_line, ingredients)
            except ParseError as err:
                # TODO: handle error
                logger.debug("ERRRRRRROOOOOOOORRRRR %s", err)
                continue
            parsed_line = parsed.log_line
            logger.debug('Parsed line: "%s"', parsed_line)
            ingredient = parsed_line.ingredient

            data_values = _get_data_values(data)
            logger.debug('DataValues: %s', data_values)
            for key, value in data_values.items():
                if key.startswith("$/"):
                    unit = key[2:]
                    amount = 1
                    break
            else:
                try:
                    value = data_values['$']
                except KeyError:
                    continue
                amount = parsed_line.amount
                unit = parsed_line.unit

            try:
                prices[ingredient.name] = value / ingredient.convert(
                    amount, unit, ingredient.sample_unit)
            except CantConvert as err:
                pass
                # TODO: handl error

    return prices


RE_KEY_VALUE = r'(?P<key>[^\d.]+)\s*(?P<value>[\d.]+)'
RE_VALUE_KEY = r'(?P<value>[\d.]+)\s*(?P<key>[^\d.]+)'


def _get_data_values(data):
    values = {}
    for data_bit in data.split(','):
        data_bit = data_bit.strip()
        mobj = (re.search(RE_KEY_VALUE, data_bit) or
                re.search(RE_VALUE_KEY, data_bit))
        if not mobj:
            continue
        try:
            values[mobj.group('key').strip()] = float(mobj.group('value'))
        except ValueError:
            continue
    return values
