#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=protected-access,invalid-name
from __future__ import absolute_import, unicode_literals, division

import logging

from pignacio_scripts.testing import TestCase

from vld.objects import LogLine
from vld.parse import parse_log_line, ParseError

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ParseLogLineTests(TestCase):
    def _test_parse(self, string, name, amount, unit, **kwargs):
        self.assertEqual(parse_log_line(string, **kwargs),
                         LogLine(name=name,
                                 amount=amount,
                                 unit=unit))

    def test_comma_parse(self):
        self._test_parse("the ing, 1 unit", "the ing", 1, "unit")

    def test_nothing_parse(self):
        self._test_parse("1 unit the ing", "the ing", 1, "unit")

    def test_of_parse(self):
        self._test_parse("1 unit of the ing", "the ing", 1, "unit")

    def test_de_parse(self):
        self._test_parse("1 unit de the ing", "the ing", 1, "unit")

    def test_nothing_float_amount(self):
        self._test_parse("1.5 unit the ing", "the ing", 1.5, "unit")

    def test_of_float_amount(self):
        self._test_parse("1.5 unit of the ing", "the ing", 1.5, "unit")

    def test_de_float_amount(self):
        self._test_parse("1.5 unit de the ing", "the ing", 1.5, "unit")

    def test_comma_float_amount(self):
        self._test_parse("the ing, 0.5 unit", "the ing", 0.5, "unit")

    def test_of_fraction_amount(self):
        self._test_parse("3/2 unit of the ing", "the ing", 1.5, "unit")

    def test_de_fraction_amount(self):
        self._test_parse("3/2 unit de the ing", "the ing", 1.5, "unit")

    def test_nothing_fraction_amount(self):
        self._test_parse("3/2 unit the ing", "the ing", 1.5, "unit")

    def test_comma_fraction_amount(self):
        self._test_parse("the ing, 1/2 unit", "the ing", 0.5, "unit")

    def test_fraction_amount_spaced(self):
        self._test_parse("the ing, 1 / 2 unit", "the ing", 0.5, "unit")

    def test_valid_unit(self):
        valid_units = ('u', )
        self._test_parse("1 u the ing", "the ing", 1, "u",
                         valid_units=valid_units)

    def test_valid_unit_with_spaces(self):
        valid_units = ('big u', )
        self._test_parse("1 big u the ing", "the ing", 1, "big u",
                         valid_units=valid_units)

    def test_one_unit_is_prefix_of_another(self):
        valid_units = ('filet', 'filet grande', )
        self._test_parse("1 filet grande merluza", "merluza", 1,
                         "filet grande",
                         valid_units=valid_units)

    def test_invalid_unit(self):
        valid_units = ('u', )
        self.assertRaisesRegexp(ParseError, "is not a valid log line",
                                parse_log_line, "1 g the ing",
                                valid_units=valid_units)

    def test_empty_unit(self):
        self._test_parse("1 huevo", "huevo", 1, "<empty>",
                         empty_unit="<empty>", )

    def test_empty_unit_fails_by_default(self):
        self.assertRaises(ParseError, parse_log_line, "1 grande")

    def test_unit_plurals(self):
        self._test_parse("2 gs the ing", "the ing", 2, "g", valid_units=("g",))
