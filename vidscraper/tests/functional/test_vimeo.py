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

import datetime
import unittest

from vidscraper.suites.vimeo import VimeoSuite


class VimeoFunctionalTestCase(unittest.TestCase):

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
                u'<object width="400" height="300">\
<param name="allowfullscreen" value="true" />\
<param name="allowscriptaccess" value="always" />\
<param name="movie"\
 value="http://vimeo.com/moogaloop.swf?clip_id=7981161&amp;\
server=vimeo.com&amp;show_title=0&amp;show_byline=0&amp;show_portrait=0&amp;\
color=&amp;fullscreen=1&amp;autoplay=0&amp;loop=0" />\
<embed src="http://vimeo.com/moogaloop.swf?clip_id=7981161&amp;\
server=vimeo.com&amp;show_title=0&amp;show_byline=0&amp;show_portrait=0&amp;\
color=&amp;fullscreen=1&amp;autoplay=0&amp;loop=0"\
 type="application/x-shockwave-flash" allowfullscreen="true"\
 allowscriptaccess="always" width="400" height="300"></embed></object>\
<p><a href="http://vimeo.com/7981161">Tishana - Pro-Choicers on Stupak</a>\
 from <a href="http://vimeo.com/user1751935">Latoya Peterson</a> on\
 <a href="http://vimeo.com">Vimeo</a>.</p>',
            'file_url_mimetype': u'video/x-flv',
            'flash_enclosure_url':
                u'http://vimeo.com/moogaloop.swf?clip_id=7981161',
            'guid': 'tag:vimeo,2009-12-04:clip7981161',
            'link': u'http://vimeo.com/7981161',
            'publish_datetime': datetime.datetime(2009, 12, 4, 8, 23, 47),
            'tags': ['Stupak-Pitts', 'Pro-Choice'],
            'thumbnail_url':
                u'http://b.vimeocdn.com/ts/360/198/36019806_640.jpg',
            'title': u'Tishana - Pro-Choicers on Stupak',
            'url': u'http://vimeo.com/7981161',
            'user': u'Latoya Peterson',
            'user_url': u'http://vimeo.com/user1751935'
            }

        for key, value in expected.items():
            self.assertEqual(value, getattr(video, key))

        # check file_url_*
        self.assertTrue('moogaloop' in video.file_url)
        self.assertTrue((video.file_url_expires -
                         datetime.datetime.utcnow()) > datetime.timedelta(
                hours=5),
                        'Not more than 5hrs in the future\n\
difference:\t%r\nexpires:\t%r\nnow:\t\t%r' % (
                video.file_url_expires - datetime.datetime.utcnow(),
                video.file_url_expires, datetime.datetime.utcnow()))

    def test_feed(self):
        feed_url = 'http://vimeo.com/user1751935/videos/'
        feed = self.suite.get_feed(feed_url)
        feed.load()
        expected = {
            'url': u'http://vimeo.com/api/v2/user1751935/videos.json',
            'title': u"Latoya Peterson's videos on Vimeo",
            'description': u'',
            'webpage': u'http://vimeo.com/user1751935/videos',
            'thumbnail_url':
                u'http://a.vimeocdn.com/images_v6/portraits/\
portrait_300_blue.png',
            }
        for key, value in expected.items():
            self.assertEqual(value, getattr(feed, key), '%s: %r != %r' % (
                    key, value, getattr(feed, key)))

        self.assertTrue(feed.entry_count > 30, feed.entry_count)
