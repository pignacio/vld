#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import logging

from var_log_dieta.objects import LogLine, LogData
from var_log_dieta.conversions import CantConvert

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ParseError(Exception):
    pass


def parse_log_line(line):
    line = line.strip()
    try:
        name, quantity = line.split(',', 1)
    except ValueError:
        raise ParseError("Invalid log line: no ',': '{}'".format(line))
    try:
        amount, unit = quantity.split(None, 1)
    except ValueError:
        raise ParseError(
            "Could not parse amount and unit from '{}'".format(quantity))
    try:
        amount = float(amount)
    except ValueError:
        raise ParseError('Invalid amount: "%s"', amount)
    return LogLine(name=name, amount=amount, unit=unit)


def parse_log_data(line, ingredients):
    parsed = parse_log_line(line)

    try:
        ingredient = ingredients[parsed.name]
    except KeyError:
        raise ParseError('Invalid ingredient: "%s"', parsed.name)
    try:
        nut_value = ingredient.get_nutritional_value(parsed.amount,
                                                     parsed.unit)
    except CantConvert as err:
        raise ParseError(str(err))

    return LogData(
        name='{}, {} {}'.format(ingredient.name, parsed.amount, parsed.unit),
        nutritional_value=nut_value)
