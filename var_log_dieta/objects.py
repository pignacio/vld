#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import collections
import logging

from pignacio_scripts.namedtuple import namedtuple_with_defaults

from .constants import DEFAULT_CONVERSIONS
from .conversions import get_conversion_table, CantConvert

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

LogData = namedtuple_with_defaults('LogData', ['name', 'nutritional_value',
                                               'parts'],
                                   defaults=lambda: {'parts': []})
LogLine = collections.namedtuple('LogLine', ['name', 'amount', 'unit'])

_NUTRITIONAL_VALUE_FIELDS = [
    'calories',
    'carbs',
    'sugar',
    'protein',
    'fat',
    'trans_fat',
    'saturated_fat',
    'fiber'
]  # yapf: disable
_NutritionalValue = namedtuple_with_defaults(
    'NutritionalValue',
    _NUTRITIONAL_VALUE_FIELDS,
    defaults={f: None for f in _NUTRITIONAL_VALUE_FIELDS}
)  # yapf: disable


class NutritionalValue(_NutritionalValue):
    UNKNOWN = None

    @classmethod
    def from_json(cls, jobj):
        return cls(**jobj)

    @classmethod
    def sum(cls, values):
        values_sum = [0] * len(cls._fields)
        for n_value in values:
            for index, value in enumerate(n_value):
                if value is not None:
                    values_sum[index] += value
        return cls(*values_sum)


NutritionalValue.UNKNOWN = NutritionalValue()

_Ingredient = namedtuple_with_defaults(
    'Ingredient',
    [
        'name',
        'sample_size',
        'sample_value',
        'sample_unit',
        'conversions',
    ],
    defaults={
        'conversions': {},
    }
)  # yapf: disable


class Ingredient(_Ingredient):
    def __init__(self, *args, **kwargs):
        super(Ingredient, self).__init__(*args, **kwargs)
        self.__conversion_table = None

    @classmethod
    def from_json(cls, jobj):
        jobj['sample_value'] = NutritionalValue.from_json(jobj['sample_value'])
        return cls(**jobj)

    def as_json(self):
        res = self._asdict()
        res['sample_value'] = res['sample_value']._asdict()
        return res

    def get_nutritional_value(self, amount, unit):
        if self.__conversion_table is None:
            self.__conversion_table = get_conversion_table(self.conversions,
                                                           DEFAULT_CONVERSIONS)
        try:
            unit_factor = self.__conversion_table[unit][self.sample_unit]
        except KeyError:
            raise CantConvert("Cannot convert '{}' from '{}' to '{}'".format(
                self.name, self.sample_unit, unit))

        factor = amount / self.sample_size * unit_factor
        new_values = {
            k: v * factor
            for k, v in self.sample_value._asdict().items() if v is not None
        }

        return self.sample_value._replace(**new_values)