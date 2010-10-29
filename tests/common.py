# encoding=UTF-8
# Copyright © 2010 Jakub Wilk <jwilk@jwilk.net>
#
# This package is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This package is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

import contextlib
import difflib

from nose.tools import __all__
from nose.tools import *

def assert_ml_equal(first, second, msg='Strings differ'):
    '''Assert that two multi-line strings are equal.'''
    assert_true(isinstance(first, basestring), 'First argument is not a string')
    assert_true(isinstance(second, basestring), 'Second argument is not a string')
    if first == second:
        return
    first = first.splitlines(True)
    second = second.splitlines(True)
    diff = '\n' + ''.join(difflib.unified_diff(first, second))
    raise AssertionError(msg + diff)

@contextlib.contextmanager
def interim(obj, **override):
    copy = dict((key, getattr(obj, key)) for key in override)
    for key, value in override.iteritems():
        setattr(obj, key, value)
    try:
        yield
    finally:
        for key, value in copy.iteritems():
            setattr(obj, key, value)

def try_run(f, *args, **kwargs):
    '''Catch SystemExit etc.'''
    try:
        f(*args, **kwargs)
    except SystemExit, ex:
        return ex.code
    else:
        return 0

__all__ = list(__all__) + ['assert_ml_equal', 'interim', 'try_run']

# vim:ts=4 sw=4 et