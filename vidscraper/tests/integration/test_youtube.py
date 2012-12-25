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

from vidscraper.suites.youtube import Suite
from vidscraper.tests.base import BaseTestCase


class YouTubeIntegrationTestCase(BaseTestCase):

    def setUp(self):
        self.suite = Suite()

    def test_video(self):
        video_url = u'http://www.youtube.com/watch?v=J_DV9b0x7v4'
        video = self.suite.get_video(video_url)
        video.load()
        expected = {
            'publish_datetime': datetime.datetime(2007, 5, 7, 22, 15, 21),
            'license': u'http://www.youtube.com/t/terms',
            'embed_code': u'<iframe width="459" height="344" src="http://www.youtube.com/embed/J_DV9b0x7v4?feature=oembed" frameborder="0" allowfullscreen></iframe>',
            'description': u"""English:
do-do-do-oo, yeah-yeah-yeah-yeah

We wonder are you ready to join us now
hands in the air
we will show you how
come and try
caramell will be your guide

So come and move your hips sing wha-a-a
look at hips, do it La-la-la
you and me can sing this melody

Oh-wa-a-a-a
Dance to the beat
Wave your hands together
Come feel the heat forever and forever
Listen and learn it is time for prancing
Now we are here with caramel dancing

O-o-oa-oa
O-o-oa-oa-a-a
O-o-oa-oa
O-o-oa-oa-a-a

From Sweden to UK we will bring our song, Australia, USA and people of Hong Kong.
They have heard this meaning all around the world

So come and move your hips sing wha-a-a
Look at your hips, do it La-la-la
You and me can sing this melody

So come and dance to the beat
Wave your hands together
Come feel the heat forever and forever
Listen and learn it is time for prancing
Now we are here with caramel dancing

(Dance to the beat
wave your hands together
come feel the heat forever and forever
listen and learn it is time for prancing
now we are here with caramel dancing)

U-u-ua-ua
U-u-ua-ua-a-a
U-u-ua-ua
U-u-ua-ua-a-a

So come and dance to the beat
Wave your hands together
Come feel the heat forever and forever
Listen and learn it is time for prancing
Now we are here with caramel dancing...
Dance to the beat
Wave your hands together
Come feel the heat forever and forever
Listen and learn it is time for prancing
Now we are here with caramel dancing 

Swedish:
Vi undrar \xe4r ni redo att vara med
Armarna upp nu ska ni f\xe5 se
Kom igen
Vem som helst kan vara med

S\xe5 r\xf6r p\xe5 era f\xf6tter
Oa-a-a
Och vicka era h\xf6fter
O-la-la-la
G\xf6r som vi
Till denna melodi

Dansa med oss
Klappa era h\xe4nder
G\xf6r som vi g\xf6r
Ta n\xe5gra steg \xe5t v\xe4nster
Lyssna och l\xe4r
Missa inte chansen
Nu \xe4r vi h\xe4r med
Caramelldansen
O-o-oa-oa...

Det blir en sensation \xf6verallt f\xf6rst\xe5s
P\xe5 fester kommer alla att sl\xe4ppa loss
Kom igen
Nu tar vi stegen om igen

S\xe5 r\xf6r p\xe5 era f\xf6tter
Oa-a-a
Och vicka era h\xf6fter
O-la-la-la
G\xf6r som vi
Till denna melodi

S\xe5 kom och
Dansa med oss
Klappa era h\xe4nder
G\xf6r som vi g\xf6r
Ta n\xe5gra steg \xe5t v\xe4nster
Lyssna och l\xe4r
Missa inte chansen
Nu \xe4r vi h\xe4r med
Caramelldansen

Dansa med oss
Klappa era h\xe4nder
G\xf6r som vi g\xf6r
Ta n\xe5gra steg \xe5t v\xe4nster
Lyssna och l\xe4r
Missa inte chansen
Nu \xe4r vi h\xe4r med
Caramelldansen""",
            'flash_enclosure_url': u'http://www.youtube.com/watch?v=J_DV9b0x7v4&feature=youtube_gdata_player',
            'user_url': u'http://www.youtube.com/user/DrunkenVuko',
            'url': u'http://www.youtube.com/watch?v=J_DV9b0x7v4',
            'fields': ['title', 'description', 'publish_datetime',
                       'flash_enclosure_url', 'is_embeddable', 'embed_code',
                       'thumbnail_url', 'user', 'user_url', 'tags', 'link',
                       'guid', 'license', 'files'],
            'title': u'CaramellDansen (Full Version + Lyrics)',
            'thumbnail_url': 'http://i3.ytimg.com/vi/J_DV9b0x7v4/hqdefault.jpg',
            'link': u'http://www.youtube.com/watch?v=J_DV9b0x7v4',
            'user': u'DrunkenVuko',
            'guid': u'http://gdata.youtube.com/feeds/api/videos/J_DV9b0x7v4',
            'tags': [u'caramell', u'dance', u'dansen', u'hip', u'hop',
                     u's\xfcchtig', u'geil', u'cool', u'lustig', u'manga',
                     u'schweden', u'anime', u'musik', u'music', u'funny',
                     u'caramelldansen', u'U-U-U-Aua', u'Dance']
            }
        for key, value in expected.items():
            self.assertEqual(value, getattr(video, key))

        # check file_url_*
        self.assertGreater(len(video.files), 0)
        video_file = video.files[0]
        self.assertEqual(video_file.mime_type, 'video/mp4')
        self.assertTrue('videoplayback' in video_file.url)
        self.assertTrue((video_file.expires -
                         datetime.datetime.utcnow()) > datetime.timedelta(
                hours=4), video_file.expires - datetime.datetime.utcnow())

    def test_video__18936(self):
        video_url = 'http://www.youtube.com/watch?v=YquEJpyZ_3U'
        video = self.suite.get_video(video_url, fields=['description'])
        video.load()
        self.assertEqual(video.description,
                         "Like dolphins, whales communicate using sound. \
Humpbacks especially have extremely complex communication systems.")

    def test_feed(self):
        feed_url = 'http://www.youtube.com/user/AssociatedPress'
        feed = self.suite.get_feed(feed_url)
        feed.load()
        expected = {
            'url': 'http://www.youtube.com/user/AssociatedPress',
            'title': u'Uploads by AssociatedPress',
            'description': None,
            'thumbnail_url': u'http://www.youtube.com/img/pic_youtubelogo_123x63.gif',
            'guid': u'tag:youtube.com,2008:user:AssociatedPress:uploads',
            }
        data = dict((key, getattr(feed, key)) for key in expected)
        self.assertEqual(data, expected)

        # YouTube changes the channel URL sometimes, so just make sure it's
        # there
        self.assertTrue(feed.webpage)
        self.assertTrue(feed.video_count > 55000, feed.video_count)

    def test_feed__18790(self):
        feed_url = 'http://www.youtube.com/user/DukeJewishStudies/videos'
        feed = self.suite.get_feed(feed_url)
        feed.load()
        self.assertEqual(feed.title, 'Uploads by DukeJewishStudies')

    def test_feed__beyond_page_range(self):
        """If you go beyond the end of a feed, StopIteration should be raised."""
        feed_url = 'http://www.youtube.com/user/AssociatedPress'
        feed = self.suite.get_feed(feed_url, max_results=1)
        feed.load()
        new_feed = self.suite.get_feed(feed_url, start_index=feed.video_count + 1000)
        self.assertRaises(StopIteration, new_feed.next)
        self.assertTrue(new_feed.is_finished())

    def test_search__over_999(self):
        """
        If you go beyond the end of a search, StopIteration should be raised.
        YouTube searches only return up to 999 results.

        """
        search = self.suite.get_search('parrot -dead', start_index=1000)
        self.assertRaises(StopIteration, search.next)
        self.assertTrue(search.is_finished())
