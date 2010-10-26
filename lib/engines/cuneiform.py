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

from __future__ import with_statement

import contextlib
import os
import re
import shlex
from cStringIO import StringIO

from . import common
from .. import errors
from .. import image_io
from .. import ipc
from .. import temporary
from .. import utils

_default_language = 'eng'
_language_pattern = re.compile('^[a-z]{3}(-[a-z]+)?$')
_language_info_pattern = re.compile(r"^Supported languages: (.*)[.]$")

_cuneiform_to_iso = dict(
    ger='deu',
    ruseng='rus-eng',  # mixed Russian-English
)

_iso_to_cuneiform = dict((y, x) for x, y in _cuneiform_to_iso.iteritems())

def cuneiform_to_iso(language):
    return _cuneiform_to_iso.get(language, language)

def iso_to_cuneiform(language):
    return _iso_to_cuneiform.get(language, language)

class Engine(common.Engine):

    name = 'cuneiform'
    image_format = image_io.BMP
    output_format = 'html'

    executable = utils.property('cuneiform')
    extra_args = utils.property([], shlex.split)
    fix_html = utils.property(0, int)

    def __init__(self, *args, **kwargs):
        assert args == ()
        common.Engine.__init__(self, *args, **kwargs)
        try:
            self._languages = list(self._get_languages())
        except errors.UnknownLanguageList:
            raise errors.EngineNotFound(self.name)
        # Import hocr late, so that importing lxml is not triggered if
        # Cuneiform is not used.
        from .. import hocr
        self._hocr = hocr

    def _get_languages(self):
        try:
            cuneiform = ipc.Subprocess([self.executable, '-l'],
                stdout=ipc.PIPE,
                stderr=ipc.PIPE,
            )
        except OSError:
            raise errors.UnknownLanguageList
        try:
            for line in cuneiform.stdout:
                m = _language_info_pattern.match(line)
                if m is None:
                    continue
                return map(cuneiform_to_iso, m.group(1).split())
        finally:
            try:
                cuneiform.wait()
            except ipc.CalledProcessError:
                pass
            else:
                raise errors.UnknownLanguageList
        raise errors.UnknownLanguageList

    @classmethod
    def get_default_language(cls):
        return _default_language

    def has_language(self, language):
        language = cuneiform_to_iso(language)
        if not _language_pattern.match(language):
            raise errors.InvalidLanguageId(language)
        return language in self._languages

    def list_languages(self):
        return iter(self._languages)

    @contextlib.contextmanager
    def recognize(self, image, language, *args, **kwargs):
        with temporary.directory() as hocr_directory:
            # A separate non-world-writable directory is needed, as Cuneiform
            # can create additional files, e.g. images.
            hocr_file_name = os.path.join(hocr_directory, 'ocr.html')
            worker = ipc.Subprocess(
                [self.executable, '-l', iso_to_cuneiform(language), '-f', 'hocr', '-o', hocr_file_name] + self.extra_args + [image.name],
                stdin=ipc.PIPE,
                stdout=ipc.PIPE,
            )
            worker.stdin.close()
            worker.wait()
            with open(hocr_file_name, 'r') as hocr_file:
                if not self.fix_html:
                    yield hocr_file
                    return
                contents = hocr_file.read()
        # Sometimes Cuneiform returns files with broken encoding or with control
        # characters: https://bugs.launchpad.net/cuneiform-linux/+bug/585418
        # Let's fix it.
        # FIXME: This work-around is ugly and should be dropped at some point.
        contents = utils.sanitize_utf8(contents)
        with contextlib.closing(StringIO(contents)) as hocr_file:
            yield hocr_file

    def extract_text(self, *args, **kwargs):
        return self._hocr.extract_text(*args, **kwargs)

# vim:ts=4 sw=4 et
