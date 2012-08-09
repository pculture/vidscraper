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

from vidscraper import auto_scrape, auto_search, auto_feed
from vidscraper.tests.base import BaseTestCase


class AutoIntegrationTestCase(BaseTestCase):
    def test_auto_scrape(self):
        video = auto_scrape("http://www.youtube.com/watch?v=J_DV9b0x7v4")
        self.assertEqual(video.title,
                         u'CaramellDansen (Full Version + Lyrics)')
        self.assertGreater(len(video.files), 0)
        self.assertTrue(video.files[0].url)
        self.assertEqual(video.files[0].mime_type, u'video/mp4')
        self.assertTrue(
            video.files[0].expires - datetime.datetime.now() >
            datetime.timedelta(hours=1))

    def test_auto_search(self):
        searches = auto_search('parrot -dead', max_results=20)
        results = []
        for search in searches:
            videos = list(search)
            self.assertTrue(len(videos) <= 20,
                            "{0} search has too many results ({1})".format(
                                search.__class__.__name__, len(videos)))
            results.extend(videos)
        self.assertTrue(len(videos) > 0)

    def test_auto_feed(self):
        max_results = 20
        feed = auto_feed("http://youtube.com/AssociatedPress",
                         max_results=max_results)
        self.assertEqual(feed.url,
                         "http://youtube.com/AssociatedPress")
        self.assertEqual(feed.url_data, {'username': 'AssociatedPress'})
        feed.load()
        self.assertEqual(feed.title, 'Uploads by AssociatedPress')
        self.assertEqual(
            feed.thumbnail_url,
            'http://www.youtube.com/img/pic_youtubelogo_123x63.gif')
        # YouTube changes this sometimes, so just make sure it's there
        self.assertTrue(feed.webpage)
        self.assertTrue(feed.etag is not None)
        self.assertTrue(feed.video_count > 55000)
        self.assertEqual(feed.guid,
                         u'tag:youtube.com,2008:user:AssociatedPress:uploads')
        videos = list(feed)
        self.assertEqual(len(videos), max_results)
