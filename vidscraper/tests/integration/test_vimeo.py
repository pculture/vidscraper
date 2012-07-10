# Copyright 2012 - Participatory Culture Foundation
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

import warnings
import datetime

from vidscraper.suites.vimeo import VimeoSuite
from vidscraper.tests.base import BaseTestCase


class VimeoIntegrationTestCase(BaseTestCase):

    def setUp(self):
        self.suite = VimeoSuite()

    def test_video(self):
        video_url = u'http://vimeo.com/7981161'
        video = self.suite.get_video(video_url)
        video.load()
        expected = {
            'description':
                'Tishana from SPARK Reproductive Justice talking about the \
right to choose after the National Day of Action Rally to Stop Stupak-Pitts, \
12.2.2009',
            'embed_code':
                (u'<iframe src="http://player.vimeo.com/video/7981161" '
                 'width="320" height="240" frameborder="0" '
                 'webkitAllowFullScreen allowFullScreen></iframe>'),
            'flash_enclosure_url':
                u'http://vimeo.com/moogaloop.swf?clip_id=7981161',
            'guid': 'tag:vimeo,2009-12-04:clip7981161',
            'link': u'http://vimeo.com/7981161',
            'publish_datetime': datetime.datetime(2009, 12, 4, 8, 23, 47),
            'tags': ['Stupak-Pitts', 'Pro-Choice'],
            'thumbnail_url':
                u'http://b.vimeocdn.com/ts/360/198/36019806_200.jpg',
            'title': u'Tishana - Pro-Choicers on Stupak',
            'url': u'http://vimeo.com/7981161',
            'user': u'Latoya Peterson',
            'user_url': u'http://vimeo.com/user1751935'
            }

        for key, value in expected.items():
            self.assertEqual(value, getattr(video, key))

    def test_video_file_url(self):
        # XXX fix this with real API support
        message = 'Vimeo file_url support is currently broken'
        if hasattr(self, 'skipTest'):
            self.skipTest(message)
        else:
            warnings.warn(message)
            return
        video_url = u'http://vimeo.com/7981161'
        video = self.suite.get_video(video_url)
        video.load()
        self.assertEqual(video.files[0].mime_type, u'video/x-flv')
        self.assertTrue('moogaloop' in video.files[0].url)
        self.assertTrue((video.files[0].expires -
                         datetime.datetime.utcnow()) > datetime.timedelta(
                hours=5),
                        'Not more than 5hrs in the future\n\
difference:\t%r\nexpires:\t%r\nnow:\t\t%r' % (
                video.files[0].expires - datetime.datetime.utcnow(),
                video.files[0].expires, datetime.datetime.utcnow()))

    def test_feed(self):
        feed_url = 'http://vimeo.com/user1751935/videos/'
        feed = self.suite.get_feed(feed_url)
        feed.load()
        expected = {
            'title': u"Latoya Peterson's videos",
            'description': u'',
            'webpage': u'http://vimeo.com/user1751935/videos',
            'thumbnail_url':
                u'http://a.vimeocdn.com/images_v6/portraits/\
portrait_300_blue.png',
            }
        for key, value in expected.items():
            self.assertEqual(value, getattr(feed, key), '%s: %r != %r' % (
                    key, value, getattr(feed, key)))

        self.assertTrue(feed.video_count > 30, feed.video_count)
