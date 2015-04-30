#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import collections
import itertools
import logging

__all__ = ['get_conversion_table']

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class DuplicateConversion(Exception):
    pass


class CantConvert(Exception):
    pass


class Conversions(object):
    def __init__(self):
        self._parents = {}
        self._factors = collections.defaultdict(dict)

    def _see(self, unit):
        if unit in self._parents:
            return
        self._put(unit, unit, 1.0)

    def _put(self, source, dest, factor):
        self._parents[dest] = source
        self._factors[source][dest] = factor

    def _checked_put(self, source, dest, factor):
        try:
            previous = self._factors[source][dest]
        except KeyError:
            self._put(source, dest, factor)
        else:
            if abs(previous - factor) > 1e-5:
                raise DuplicateConversion("{} -> {}: {} != {}".format(
                    source, dest, previous, factor))

    def _steal(self, source, victim, source_victim_factor):
        if source == victim:
            raise ValueError(
                "Trying to steal form theyself: {}".format(source))
        for dest, victim_dest_factor in self._factors[victim].items():
            self._checked_put(source, dest,
                              source_victim_factor * victim_dest_factor)
        del self._factors[victim]
        self._checked_put(source, victim, source_victim_factor)

    def add(self, source, dest, source_dest_factor):
        self._see(source)
        self._see(dest)
        source_parent = self._parents[source]
        dest_parent = self._parents[dest]
        parent_factor = (self._factors[source_parent][source] *
                         source_dest_factor / self._factors[dest_parent][dest])
        if source_parent == dest_parent:
            self._checked_put(source_parent, dest_parent, parent_factor)
        else:
            self._steal(source_parent, dest_parent, parent_factor)

    def get_conversion_table(self):
        table = collections.defaultdict(dict)

        for factors in self._factors.values():
            for source, dest in itertools.product(factors, factors):
                table[source][dest] = factors[dest] / factors[source]

        return table


def _iter_conversions(conversions):
    for source, factors in conversions.items():
        for dest, factor in factors.items():
            yield source, dest, factor


def get_conversion_table(ingredient_conversions, default_conversions):
    conversions = Conversions()
    for source, dest, factor in _iter_conversions(ingredient_conversions):
        conversions.add(source, dest, factor)

    for source, dest, factor in _iter_conversions(default_conversions):
        try:
            conversions.add(source, dest, factor)
        except DuplicateConversion:
            pass
    return conversions.get_conversion_table()
