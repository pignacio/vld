#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import logging
import re

from var_log_dieta.objects import LogLine, LogData, NutritionalValue
from var_log_dieta.conversions import CantConvert

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ParseError(Exception):
    pass


RE_INGREDIENT_COMMA_QUANTITY = r'^{ingredient_re},\s*{quantity_re}$'
RE_QUANTITY_OF_INGREDIENT = r'^{quantity_re}\s+(de |of )?{ingredient_re}$'

RE_INGREDIENT = r'(?P<ingredient>.+)'
RE_QUANTITY = r'(?P<amount>[\d.]+(?:\s*/\s*[\d.]+)?)\s*(?P<unit>{units_re})s?'


def parse_log_line(line, valid_units=None, empty_unit=None):
    line = line.strip()
    logger.debug('Parsing log line: "%s"', line)
    for regexp in [RE_INGREDIENT_COMMA_QUANTITY, RE_QUANTITY_OF_INGREDIENT]:
        if valid_units:
            # Reverse sorting so "(a|ab)" matches the full "ab"
            ored_units = "|".join(sorted(valid_units, reverse=True))
            if empty_unit:
                ored_units = "|" + ored_units
            units_re = "(?:{})".format(ored_units)
        else:
            units_re = r"\w[\w ]*?"
            if empty_unit:
                units_re = "(?:|{})".format(units_re)

        quantity_re = RE_QUANTITY.format(units_re=units_re)
        logline_re = regexp.format(ingredient_re=RE_INGREDIENT,
                                   quantity_re=quantity_re)

        logger.debug('Triying to match "%s" to :"%s"', logline_re, line)
        matchobj = re.match(logline_re, line)
        if matchobj:
            ingredient = matchobj.group("ingredient")
            amount = matchobj.group("amount")
            unit = matchobj.group("unit") or empty_unit

            try:
                # TODO(irossi): FIXME(irossi): ermahgerd, using eval!
                amount = float(eval(amount))
            except (ValueError, TypeError, SyntaxError):
                raise ParseError('"{}" is not a valid amount.'.format(amount))

            return LogLine(name=ingredient, amount=amount, unit=unit)
        else:
            logger.debug('"%s" did not match "%s"', logline_re, line)
    raise ParseError('"{}" is not a valid log line.'.format(line))


def _parse_log_line(line):
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
        raise ParseError('Invalid amount: "{}"'.format(amount))
    return LogLine(name=name, amount=amount, unit=unit)


def parse_log_data(line, ingredients):
    try:
        line, comment = line.split('#', 1)
    except ValueError:
        line, comment = line, ''
    try:
        return _parse_log_data(line, ingredients)
    except ParseError:
        value = NutritionalValue.from_line(comment)
        if value != NutritionalValue.UNKNOWN:
            return LogData(name=line, nutritional_value=value)
        raise


def _parse_log_data(line, ingredients):
    parsed = parse_log_line(line)
    try:
        ingredient = ingredients[parsed.name]
    except KeyError:
        raise ParseError('Invalid ingredient: "{}"'.format(parsed.name))
    try:
        nut_value = ingredient.get_nutritional_value(parsed.amount,
                                                     parsed.unit)
    except CantConvert as err:
        raise ParseError(str(err))

    return LogData(
        name='{}, {} {}'.format(ingredient.name, parsed.amount, parsed.unit),
        nutritional_value=nut_value,
        log_line=parsed._replace(ingredient=ingredient), )
