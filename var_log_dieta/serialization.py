#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import json
import logging
import os

from .objects import Ingredient

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def load_ingredients(directory):
    if not os.path.isdir(directory):
        raise ValueError(
            "Invalid ingredient directory: '{}'".format(directory))
    logger.info("Loading ingredients from '%s'", directory)
    ingredients = []
    for path, subdirs, filenames in os.walk(directory):
        for filename in filenames:
            fullpath = os.path.join(path, filename)
            logging.debug(" - Parsing ingredients from '%s'", fullpath)
            with open(fullpath) as fin:
                json_list = json.load(fin)
            ingredients.extend([Ingredient.from_json(data)
                                for data in json_list])

    logger.info("Loaded %d ingredients", len(ingredients))
    return ingredients
