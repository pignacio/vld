#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import logging
from unidecode import unidecode

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class IngredientMap(object):
    def __init__(self, ingredients):
        self._ingredients = {
            self._normalize_name(i.name): i
            for i in ingredients
        }

    def __getitem__(self, name):
        return self._ingredients[self._normalize_name(name)]

    @staticmethod
    def _normalize_name(name):
        return unidecode(name.strip()).lower()
