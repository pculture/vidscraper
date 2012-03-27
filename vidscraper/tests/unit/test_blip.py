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
import urllib
import urlparse

from vidscraper.errors import CantIdentifyUrl
from vidscraper.videos import Video
from vidscraper.suites import OEmbedMethod
from vidscraper.suites.blip import BlipSuite, BlipApiMethod
from vidscraper.tests.base import BaseTestCase


DISQUS_DATA = {
    'guid': u'4809E60A-C2AB-11DF-BBAC-A6337D0214E0',
    'link': "http://blip.tv/file/4135225",
    'title': "Scaling the World's Largest Django Application",
    'description': "<p>Disqus, one of the largest Django applications in "
                    "the world, will explain how they deal with scaling "
                    "complexities in a small startup.</p>",
    'file_url': "http://blip.tv/file/get/Robertlofthouse-ScalingTheWorldsLargestDjangoApplication558.ogv",
    'embed_code': '<embed src="http://blip.tv/play/AYH9xikC" '
                    'type="application/x-shockwave-flash" width="480" '
                    'height="390" wmode="transparent" '
                    'allowscriptaccess="always" allowfullscreen="true" >'
                    '</embed>',
    'publish_datetime': datetime.datetime(2010, 9, 17, 22, 31, 14),
    'thumbnail_url': "http://a.images.blip.tv/Robertlofthouse-ScalingTheWorldsLargestDjangoApplication538.png",
    'tags': [u'shmpe', u'djangocon', u'2010'],
    'user': 'djangocon',
    'user_url': 'http://djangocon.blip.tv/',
    'license': 'http://creativecommons.org/licenses/by-nc-sa/3.0/',
}

class BlipTestCase(BaseTestCase):
    def setUp(self):
        self.suite = BlipSuite()


class BlipApiTestCase(BlipTestCase):
    def setUp(self):
        BlipTestCase.setUp(self)
        self.method = BlipApiMethod()
        self.base_url = "http://blip.tv/djangocon/lightning-talks-day-1-4167881"
        self.video = self.suite.get_video(url=self.base_url)

    def _test_video_api_url(self, video):
        api_url = self.method.get_url(video)
        parsed_url = urlparse.urlparse(api_url)
        self.assertEqual(parsed_url[2], "/rss/4167881")

    def test_get_url(self):
        self._test_video_api_url(self.video)

    def test_get_url_overrides(self):
        """GET parameters shouldn't affect the outcome."""
        video = self.suite.get_video(url="%s?skin=json" % self.base_url)
        self._test_video_api_url(video)

    def test_get_url_old_url(self):
        """Old urls should be parsed differently."""
        self.video.url = 'http://blip.tv/file/1077145/'
        api_url = self.method.get_url(self.video)
        parsed_url = urlparse.urlsplit(api_url)
        self.assertEqual(parsed_url[2], '/file/1077145/')
        self.assertEqual(parsed_url[3], 'skin=rss')

    def test_process(self):
        api_file = self.get_data_file('blip/api.rss')
        response = self.get_response(api_file.read())
        data = self.method.process(response)
        self.assertEqual(set(data), self.method.fields)
        self.assertEqual(data, DISQUS_DATA)


class BlipFeedTestCase(BlipTestCase):
    def setUp(self):
        BlipTestCase.setUp(self)
        self.feed_url = 'http://blip.tv/djangocon'
        self.feed = self.suite.get_feed(self.feed_url)
        self.feed_data = self.get_data_file('blip/feed.rss')
        self.feed.handle_first_response(self.suite.get_feed_response(
                self.feed, self.feed_data))

    def test_get_feed_url(self):
        self.assertEqual(self.suite.get_feed_url(self.feed_url),
                         'http://blip.tv/djangocon/rss')
        self.assertEqual(self.suite.get_feed_url(
                'http://blip.tv/djangocon/rss'),
                         'http://blip.tv/djangocon/rss')
        self.assertEqual(self.suite.get_feed_url(
                'http://blip.tv/djangocon'),
                         'http://blip.tv/djangocon/rss')

    def test_get_feed_entries(self):
        response = self.suite.get_feed_response(self.feed, self.feed_data)
        entries = self.suite.get_feed_entries(self.feed, response)
        self.assertEqual(len(entries), 77)

    def test_parse_entry(self):
        response = self.suite.get_feed_response(self.feed, self.feed_data)
        entries = self.suite.get_feed_entries(self.feed, response)
        data = self.suite.parse_feed_entry(entries[1])
        self.assertEqual(data, DISQUS_DATA)

    def test_parse_feed(self):
        self.assertEqual(len(list(self.feed)), 77)
        for video in self.feed:
            self.assertTrue(isinstance(video, Video))

    def test_next_feed_page_url(self):
        # get_next_feed_page_url expects ``feed``, ``feed_response`` arguments.
        # feed_response is a feedparser response.
        response = self.suite.get_feed_response(self.feed, self.feed_data)
        response.href = 'http://blip.tv/nothing/here/?page=5'
        new_url = self.suite.get_next_feed_page_url(None, response)
        self.assertEqual(new_url, 'http://blip.tv/nothing/here/?page=6')
        response.href = 'http://blip.tv/nothing/here/'
        new_url = self.suite.get_next_feed_page_url(None, response)
        self.assertEqual(new_url, 'http://blip.tv/nothing/here/?page=2')
        response.href = 'http://blip.tv/nothing/here/?page=notanumber'
        new_url = self.suite.get_next_feed_page_url(None, response)
        self.assertEqual(new_url, 'http://blip.tv/nothing/here/?page=2')


class BlipSearchTestCase(BlipTestCase):
    def setUp(self):
        BlipTestCase.setUp(self)
        self.feed_data = self.get_data_file('blip/search.rss')
        self.search = self.suite.get_search('search query')

    def test_parse_search_feed(self):
        response = self.suite.get_search_response(self.search, self.feed_data)
        results = self.suite.get_search_results(self.search, response)
        self.assertTrue(len(results) > 0)

    def test_parse_result(self):
        response = self.suite.get_search_response(self.search, self.feed_data)
        results = self.suite.get_search_results(self.search, response)
        data = self.suite.parse_search_result(self.search, results[1])
        self.assertEqual(data, DISQUS_DATA)

class BlipSuiteTestCase(BlipTestCase):
    def test_mp4_not_included(self):
        self.assertFalse(self.suite.handles_video_url(
                'http://blip.tv/file/get/Miropcf-Miro20Introduction119.mp4'))
