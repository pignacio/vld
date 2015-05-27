#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import json
import logging

from vld.objects import Ingredient, NutritionalValue
from vld.utils import base_argument_parser

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def get_argument_parser():
    parser = base_argument_parser()
    parser.add_argument('name', help='Name for the new ingredient')
    parser.add_argument('-k', '--calories',
                        type=float,
                        default=None,
                        help='Calories for the new ingredient')
    parser.add_argument('-c', '--carbs',
                        type=float,
                        default=None,
                        help='Carbs for the new ingredient')
    parser.add_argument('-s', '--sugar',
                        type=float,
                        default=None,
                        help='Sugar for the new ingredient')
    parser.add_argument('-p', '--protein',
                        type=float,
                        default=None,
                        help='Protein for the new ingredient')
    parser.add_argument('-f', '--fat',
                        type=float,
                        default=None,
                        help='Total fat for the new ingredient')
    parser.add_argument('-tf', '--trans-fat',
                        type=float,
                        default=None,
                        help='Trans fat for the new ingredient')
    parser.add_argument('-sf', '--saturated-fat',
                        type=float,
                        default=None,
                        help='Saturated fat for the new ingredient')
    parser.add_argument('-df', '--fiber',
                        type=float,
                        default=None,
                        help='Dietary fiber for the new ingredient')
    parser.add_argument('--sample-size',
                        type=float,
                        default=100,
                        help='Sample size for the new ingredient')
    parser.add_argument('--sample-unit',
                        default='g',
                        help='Sample unit for the new ingredient')
    parser.add_argument('--category',
                        action='append',
                        default=[],
                        help='Category for the new ingredient')
    return parser


def main(options):
    sample_value = NutritionalValue(calories=options.calories,
                                    carbs=options.carbs,
                                    sugar=options.sugar,
                                    protein=options.protein,
                                    fat=options.fat,
                                    trans_fat=options.trans_fat,
                                    saturated_fat=options.saturated_fat,
                                    fiber=options.fiber)
    ingredient = Ingredient(name=options.name,
                            sample_size=options.sample_size,
                            sample_unit=options.sample_unit,
                            sample_value=sample_value,
                            categories=options.category)
    print json.dumps(ingredient.as_json(), indent=1)
