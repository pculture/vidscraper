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
import unittest

from vidscraper.suites.google import GoogleSuite


class GoogleTestCase(unittest.TestCase):
    def setUp(self):
        self.suite = GoogleSuite()

    @property
    def data_file_dir(self):
        if not hasattr(self, '_data_file_dir'):
            test_dir = os.path.abspath(os.path.dirname(
                                                os.path.dirname(__file__)))
            self._data_file_dir = os.path.join(test_dir, 'data', 'google')
        return self._data_file_dir


class GoogleScrapeTestCase(GoogleTestCase):
    def setUp(self):
        GoogleTestCase.setUp(self)
        self.base_url = "http://video.google.com/videoplay?docid=3372610739323185039"
        self.video = self.suite.get_video(self.base_url)

    def test_get_scrape_url(self):
        self.assertEqual(self.suite.get_scrape_url(self.video), self.base_url)

    def test_parse_scrape_response(self):
        scrape_file = open(os.path.join(self.data_file_dir, 'scrape.html'))
        data = self.suite.parse_scrape_response(scrape_file.read())
        self.assertTrue(isinstance(data, dict))
        self.assertEqual(set(data), self.suite.scrape_fields)
        expected_data = {
            'title': "Tom and Jerry. Texas",
            'description': 'Tom and Jerry.',
            'embed_code': """<embed id="VideoPlayback" \
src="http://video.google.com/googleplayer.swf?docid=3372610739323185039&\
hl=en&fs=true" style="width:400px;height:326px" allowFullScreen="true" \
allowScriptAccess="always" type="application/x-shockwave-flash"> </embed>"""
        }
        for key in expected_data:
            self.assertTrue(key in data)
            self.assertEqual(data[key], expected_data[key])
