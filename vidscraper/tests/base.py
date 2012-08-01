# Copyright 2009 - Participatory Culture Foundation
#
# This file is part of vidscraper.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os

from requests.models import Response
import unittest2

import vidscraper


class BaseTestCase(unittest2.TestCase):
    def _data_file_path(self, data_file):
        root = os.path.abspath(os.path.dirname(vidscraper.__file__))
        return os.path.join(root, 'tests', 'data', data_file)

    def get_data_file(self, data_file):
        return open(self._data_file_path(data_file))

    def get_response(self, content, code=200):
        response = Response()
        response._content = content
        response.status_code = code
        return response

    def assertDictEqual(self, data, expected_data, msg=None):
        self.assertEqual(set(data), set(expected_data))
        for key in data:
            self.assertEqual(data[key], expected_data[key],
                             u'value for {key} not equal:\n'
                             u'{value} != {expected}'.format(
                                key=key, value=data[key],
                                expected=expected_data[key]))
