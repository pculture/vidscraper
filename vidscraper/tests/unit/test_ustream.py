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

from vidscraper.suites.ustream import UstreamSuite, UstreamApiMethod
from vidscraper.tests.base import BaseTestCase


class UstreamTestCase(BaseTestCase):
    def setUp(self):
        self.suite = UstreamSuite()


class UstreamApiTestCase(UstreamTestCase):
    def setUp(self):
        UstreamTestCase.setUp(self)
        self.method = UstreamApiMethod()
        self.base_url = "http://www.ustream.tv/recorded/16417223"
        self.video = self.suite.get_video(self.base_url,
                                          api_keys={'ustream_key': 'TEST_KEY'})

    def test_get_url(self):
        api_url = self.method.get_url(self.video)
        self.assertEqual(api_url,
            'http://api.ustream.tv/json/video/16417223/getInfo/?key=TEST_KEY')

    def test_process(self):
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
        api_file = self.get_data_file('ustream/api.json')
        response = self.get_response(api_file.read())
        data = self.method.process(response)
        self.assertEqual(set(data), self.method.fields)
        self.assertDictEqual(data, expected_data)
