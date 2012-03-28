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

from vidscraper.suites.ustream import UstreamSuite


class UstreamTestCase(unittest.TestCase):
    def setUp(self):
        self.suite = UstreamSuite()

    @property
    def data_file_dir(self):
        if not hasattr(self, '_data_file_dir'):
            test_dir = os.path.abspath(os.path.dirname(
                                                os.path.dirname(__file__)))
            self._data_file_dir = os.path.join(test_dir, 'data', 'ustream')
        return self._data_file_dir


class UstreamApiTestCase(UstreamTestCase):
    def setUp(self):
        UstreamTestCase.setUp(self)
        self.base_url = "http://www.ustream.tv/recorded/16417223"
        self.video = self.suite.get_video(self.base_url,
                                          api_keys={'ustream_key': 'TEST_KEY'})

    def test_get_oembed_url(self):
        url = self.suite.get_oembed_url(self.video)
        self.assertEqual(url, "http://www.ustream.tv/oembed/?url=http%3A%2F%2Fwww.ustream.tv%2Frecorded%2F16417223")

    def test_parse_oembed_response(self):
        oembed_file = open(os.path.join(self.data_file_dir, 'oembed.json'))
        data = self.suite.parse_oembed_response(oembed_file.read())
        self.assertTrue(isinstance(data, dict))
        self.assertEqual(set(data), self.suite.oembed_fields)
        expected_data = {
            'embed_code': u'<object classid="clsid:d27cdb6e-ae6d-11cf-96b8'
            '-444553540000" width="480" height="296" id="utv814986" '
            'name="utv_n_604069"><param name="flashvars" '
            'value="loc=%2F&amp;autoplay=false&amp;vid=16417223&amp;'
            'locale=en_US" /><param name="allowfullscreen" value="true" />'
            '<param name="allowscriptaccess" value="always" /><param '
            'name="src" value="http://www.ustream.tv/flash/viewer.swf" />'
            '<embed flashvars="loc=%2F&amp;autoplay=false&amp;vid=16417223&amp;'
            'locale=en_US" width="480" height="296" allowfullscreen="true" '
            'allowscriptaccess="always" id="utv814986" name="utv_n_604069" '
            'src="http://www.ustream.tv/flash/viewer.swf" '
            'type="application/x-shockwave-flash" /></object>',
            'user_url': u'http://www.ustream.tv/user/ObamaForAmerica', 'thumbnail_url': u'http://static-cdn1.ustream.tv/images/uphoto_file/5/6/5/5/56554/th/smalls2_120_56554_obama_ustream.jpg', 'user': u'ObamaForAmerica',
            'title': u'President Obama Speaks Live From His Birthday Event'
        }
        for key in expected_data:
            self.assertTrue(key in data)
            self.assertEqual(data[key], expected_data[key])

    def test_get_api_url(self):
        api_url = self.suite.get_api_url(self.video)
        self.assertEqual(api_url,
            'http://api.ustream.tv/json/video/16417223/getInfo/?key=TEST_KEY')

    def test_parse_api_response(self):
        api_file = open(os.path.join(self.data_file_dir, 'api.json'))
        data = self.suite.parse_api_response(api_file.read())
        self.assertTrue(isinstance(data, dict))
        self.assertEqual(set(data), self.suite.api_fields)
        expected_data = {
            'embed_code': u"<iframe src='http://www.ustream.tv/flash/video/"
                           "16417223' width='320' height='260' />",
            'link': u'http://www.ustream.tv/recorded/16417223',
            'description': u'President Obama Speaks Live From His Birthday Event',
            'flash_enclosure_url': u'http://www.ustream.tv/flash/video/16417223',
            'title': u'President Obama Speaks Live From His Birthday Event',
            'publish_date': datetime.datetime(2011, 8, 3, 17, 16, 55),
            'tags': [u'Barack', u'Live', u'Obama', u'Ustream', u'on'],
            'thumbnail_url': u'http://static-cdn2.ustream.tv/videopic/0/1/16/16417/16417223/1_203240_16417223_320x240_b_1:2.jpg',
            'user_url': u'http://www.ustream.tv/user/ObamaForAmerica',
            'user': u'ObamaForAmerica'
        }
        for key in expected_data:
            self.assertTrue(key in data)
            self.assertEqual(data[key], expected_data[key])
