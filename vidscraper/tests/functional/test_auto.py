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
import unittest

from vidscraper import auto_scrape, auto_search, auto_feed

class AutoFunctionalTestCase(unittest.TestCase):
    def test_auto_scrape(self):
        video = auto_scrape("http://www.youtube.com/watch?v=J_DV9b0x7v4")
        self.assertEqual(video.title,
                         u'CaramellDansen (Full Version + Lyrics)')
        self.assertNotEqual(video.file_url, None)
        self.assertEqual(video.file_url_mimetype, u'video/x-flv')
        self.assertTrue(
            video.file_url_expires - datetime.datetime.now() >
            datetime.timedelta(hours=1))

    def test_auto_search(self):
        result_lists = auto_search('parrot -dead').values()
        results = []
        for result_list in result_lists:
            results.extend(result_list)
        self.assertTrue(len(results) > 0)

    def test_auto_feed(self):
        feed = auto_feed("http://youtube.com/AssociatedPress")
        self.assertEqual(feed.url,
                         ('http://gdata.youtube.com/feeds/base/users/'
                          'AssociatedPress/uploads?alt=rss&v=2'))
        feed.load()
        self.assertEqual(feed.title, 'Uploads by AssociatedPress')
        self.assertEqual(
            feed.thumbnail_url,
            'http://www.youtube.com/img/pic_youtubelogo_123x63.gif')
        self.assertTrue('AssociatedPress' in feed.webpage)
        self.assertTrue(feed.entry_count > 50000)
