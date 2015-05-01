#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import json
import logging

from var_log_dieta.objects import Ingredient, NutritionalValue
from var_log_dieta.utils import base_argument_parser

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def get_argument_parser():
    parser = base_argument_parser()
    parser.add_argument('name', help='Name for the new ingredient')
    return parser


def main(options):
    ingredient = Ingredient(name=options.name,
                            sample_size=100,
                            sample_unit='g',
                            sample_value=NutritionalValue.UNKNOWN)
    print json.dumps(ingredient.as_json(), indent=1)
