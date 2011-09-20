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

import datetime
import os
import unittest

from vidscraper.suites.vimeo import VimeoSuite


class VimeoTestCase(unittest.TestCase):
    def setUp(self):
        self.suite = VimeoSuite()

    @property
    def data_file_dir(self):
        if not hasattr(self, '_data_file_dir'):
            test_dir = os.path.abspath(os.path.dirname(
                                                os.path.dirname(__file__)))
            self._data_file_dir = os.path.join(test_dir, 'data', 'vimeo')
        return self._data_file_dir


class VimeoApiTestCase(VimeoTestCase):
    def setUp(self):
        VimeoTestCase.setUp(self)
        self.base_url = "http://vimeo.com/2"
        self.video = self.suite.get_video(self.base_url)

    def test_get_oembed_url(self):
        url = self.suite.get_oembed_url(self.video)
        self.assertEqual(url, "http://vimeo.com/api/oembed.json?url=http%3A%2F%2Fvimeo.com%2F2")

    def test_parse_oembed_response(self):
        oembed_file = open(os.path.join(self.data_file_dir, 'oembed.json'))
        data = self.suite.parse_oembed_response(oembed_file.read())
        self.assertTrue(isinstance(data, dict))
        self.assertEqual(set(data), self.suite.oembed_fields)
        expected_data = {
            'embed_code': u'<iframe src="http://player.vimeo.com/video/2" '
                           'width="320" height="240" frameborder="0" '
                           'webkitAllowFullScreen allowFullScreen></iframe>',
            'user_url': u'http://vimeo.com/jakob',
            'thumbnail_url': u'http://b.vimeocdn.com/ts/228/979/22897998_200.jpg',
            'user': u'Jake Lodwick',
            'title': u'Good morning, universe'
        }
        for key in expected_data:
            self.assertTrue(key in data)
            self.assertEqual(data[key], expected_data[key])

    def test_get_api_url(self):
        api_url = self.suite.get_api_url(self.video)
        self.assertEqual(api_url, 'http://vimeo.com/api/v2/video/2.json')

    def test_parse_api_response(self):
        api_file = open(os.path.join(self.data_file_dir, 'api.json'))
        data = self.suite.parse_api_response(api_file.read())
        self.assertTrue(isinstance(data, dict))
        self.assertEqual(set(data), self.suite.api_fields)
        expected_data = {
            'thumbnail_url': u'http://b.vimeocdn.com/ts/228/979/22897998_200.jpg',
            'link': u'http://vimeo.com/2',
            'description': u'I shot this myself!',
            'title': u'Good morning, universe',
            'publish_date': datetime.datetime(2005, 2, 16, 23, 9, 19),
            'user_url': u'http://vimeo.com/jakob',
            'tags': [u'morning', u'bed', u'slow', u'my bedroom', u'creepy',
                     u'smile', u'fart'],
            'user': u'Jake Lodwick'
        }
        for key in expected_data:
            self.assertTrue(key in data)
            self.assertEqual(data[key], expected_data[key])
