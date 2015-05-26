#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import logging
import os
import sys

from pignacio_scripts.terminal.color import green, blue, red

from var_log_dieta.constants import DATA_DIR
from var_log_dieta.objects import NutritionalValue, CantConvert
from var_log_dieta.serialization import load_ingredients
from var_log_dieta.utils import base_argument_parser

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def get_argument_parser():
    parser = base_argument_parser()
    parser.add_argument(
        '-s', '--sort',
        action='store',
        default=None,
        type=_sort_key,
        help=('Sorting for the ingredients. Defaults ingredient name.'))
    parser.add_argument('-c', '--category',
                        help='Show only a category of ingredients.')
    #     parser.add_argument('--include-sort-value',
    #                         action='store_true',
    #                         default=False,
    #                         help=('Add a column with the sort value.'))
    #     parser.add_argument('--no-separators',
    #                         action='store_true',
    #                         default=False,
    #                         help=('Remove the column separators.'))
    return parser


def _normalize_value(ingredient):
    try:
        return ("100 g", ingredient.get_nutritional_value(100, "g"))
    except CantConvert:
        pass
    try:
        return ("100 ml", ingredient.get_nutritional_value(100, "ml"))
    except CantConvert:
        pass
    return ("{} {}".format(ingredient.sample_size, ingredient.sample_unit),
            ingredient.sample_value)


def _filter_by_category(ingredients, category):
    def _norm(category):
        return category.strip().lower()
    category = _norm(category)
    return [i for i in ingredients
            if any(category == _norm(c) for c in i.categories)]

def main(options):
    ingredients = load_ingredients(os.path.join(DATA_DIR, 'ingredients'))
    if options.category:
        ingredients = _filter_by_category(ingredients, options.category)
    if not ingredients:
        print "No ingredients :("
        return
    columns = ['name', 'amount'] + list(ingredients[0].sample_value.values())
    values = {}
    for ingredient in ingredients:
        amount, value = _normalize_value(ingredient)
        values[ingredient.name] = value.values()
        values[ingredient.name].update(
            {'name': ingredient.name,
             'amount': amount, })

    headers = {
        'calories': 'cals',
        'saturated_fat': 'sat fat',
        'trans_fat': 'trans',
        'consumed_carbs': 'cc',
        'protein': 'prot'
    }

    if options.sort:
        items = values.items()
        for _name, values in items:
            values['sort'] = options.sort(values)

        items.sort(key=lambda (n, v): v['sort'], reverse=True)
        columns.append('sort')
    else:
        items = sorted(values.items())

    table = [[headers.get(c, c) for c in columns]] + [[_stringify_cell(v[c], c)
                                                       for c in columns]
                                                      for _i, v in items]

    max_lengths = [max(len(row[x]) for row in table)
                   for x in xrange(len(columns))]
    format_strs = ["{{:>{}s}}".format(l) for l in max_lengths]

    for irow, row in enumerate(table[1:]):
        if irow % 10 == 0:
            for format_str, header in zip(format_strs, table[0]):
                sys.stdout.write(_color_cell(format_str.format(header), 0,
                                             header))
                sys.stdout.write("| ")
            print
        for icol, (format_str, cell) in enumerate(zip(format_strs, row)):
            sys.stdout.write(_color_cell(format_str.format(cell), irow + 1,
                                         columns[icol])),
            sys.stdout.write("| ")
        print


def _stringify_cell(cell, column):
    if cell is None:
        return '???'
    if isinstance(cell, float):
        if column == 'sort':
            return "{:.2f}".format(cell)
        else:
            return "{:.1f}".format(cell)
    return unicode(cell)


def _color_cell(cell, row, column):
    if row == 0:
        return blue(cell)
    if cell.strip() == '???':
        return red(cell)
    if column == 'name':
        return green(cell)
    return cell


def _sort_key(arg):
    arg = arg.strip()
    if "/" in arg:
        num, den = [NutritionalValue.expand_field(f.strip())
                    for f in arg.split("/", 1)]

        def key(values):
            v_num = values[num]
            v_den = values[den]
            if v_num is None or v_den is None:
                return None
            return v_num / (v_den + 0.001)

        return key
    else:
        field = NutritionalValue.expand_field(arg)
        return lambda v: v[field]
