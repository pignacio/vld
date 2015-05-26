#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import logging
import re

from cached_property import cached_property
from pignacio_scripts.namedtuple import namedtuple_with_defaults

from .constants import DEFAULT_CONVERSIONS
from .conversions import get_conversion_table, CantConvert

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

_LogData = namedtuple_with_defaults(
    'LogData',
    [
        'name',
        'nutritional_value',
        'parts',
        'log_line',
        'incomplete',
        'ingredient',
        'is_leaf',
    ],
    defaults=lambda: {
        'parts': [],
        'log_line': None,
        'incomplete': False,
        'ingredient': None,
        'is_leaf': False,
    }
)  # yapf: disable


class LogData(_LogData):
    __slots__ = ()

    @classmethod
    def from_parts(cls, name, parts, **kwargs):
        return cls(name=name,
                   parts=parts,
                   nutritional_value=NutritionalValue.sum(p.nutritional_value
                                                          for p in parts),
                   incomplete=any(p.incomplete for p in parts), **kwargs)


LogLine = namedtuple_with_defaults('LogLine', ['name', 'amount', 'unit',
                                               'ingredient'],
                                   defaults={'ingredient': None})

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
    _FIELD_ALIASES = {
        'k': 'calories',
        'cal': 'calories',
        'kcal': 'calories',
        'c': 'carbs',
        's': 'sugar',
        'f': 'fat',
        'sf': 'saturated_fat',
        'tf': 'trans_fat',
        'df': 'fiber',
        'p': 'protein',
        'cc': 'consumed_carbs',
    }  # yapf: disable

    __sort_fields = set(_NutritionalValue._fields + ('consumed_carbs', ))

    @property
    def consumed_carbs(self):
        return None if self.carbs is None else self.carbs - (self.fiber or 0)

    def values(self):
        res = self._asdict()
        res.update({'consumed_carbs': self.consumed_carbs, })
        return res

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

    @classmethod
    def from_line(cls, line):
        values = {}
        for part in re.split('[;,]', line):
            logger.debug('from_line: part: %s', part)
            try:
                key, value = (x.strip() for x in re.split('[:=]', part, 1))
                value = float(value)
                field = cls.expand_field(key)
            except (KeyError, ValueError):
                pass
            else:
                values[field] = value
        return cls(**values)

    @classmethod
    def expand_field(cls, short_field):
        field = cls._FIELD_ALIASES.get(short_field, short_field)
        logging.debug(
            "Expanded NutValue field: {!r} => {!r}".format(short_field, field))
        if field not in cls.__sort_fields:
            raise ValueError(
                'Invalid NutritionalValue field: "{}"'.format(short_field))
        return field


NutritionalValue.UNKNOWN = NutritionalValue()

_Ingredient = namedtuple_with_defaults(
    'Ingredient',
    [
        'name',
        'sample_size',
        'sample_value',
        'sample_unit',
        'conversions',
        'categories',
    ],
    defaults={
        'conversions': {},
        'categories': [],
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

    @cached_property
    def _conversion_table(self):
        return get_conversion_table(self.conversions, DEFAULT_CONVERSIONS)

    def convert(self, amount, unit, target_unit):
        if unit == target_unit:
            return amount
        else:
            try:
                factor = self._conversion_table[unit][target_unit]
            except KeyError:
                raise CantConvert(
                    "Cannot convert '{}' from '{}' to '{}'".format(
                        self.name, unit, target_unit))

        return amount * factor

    def get_nutritional_value(self, amount, unit):
        factor = self.convert(amount, unit,
                              self.sample_unit) / self.sample_size
        new_values = {
            k: v * factor
            for k, v in self.sample_value._asdict().items() if v is not None
        }

        return self.sample_value._replace(**new_values)
