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

import feedparser

from vidscraper.exceptions import UnhandledSearch
from vidscraper.suites import OEmbedMethod
from vidscraper.suites.blip import BlipSuite, BlipApiMethod
from vidscraper.tests.base import BaseTestCase
from vidscraper.videos import Video


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
        self.response = feedparser.parse(self.get_data_file('blip/feed.rss'))

    def test_feed_urls(self):
        valid_show_urls = (
            'http://blip.tv/djangocon',
            'http://blip.tv/djangocon/rss',
            'http://blip.tv/djangocon?skin=rss',
        )
        valid_no_show_urls = (
            'http://blip.tv',
            'http://blip.tv/rss',
            'http://blip.tv?skin=rss',
        )
        for url in valid_show_urls:
            data = self.feed.get_url_data(url)
            self.assertEqual(data, {'show': 'djangocon'})

        for url in valid_no_show_urls:
            data = self.feed.get_url_data(url)
            self.assertEqual(data, {'show': None})

    def test_get_page_url(self):
        expected = "http://blip.tv/djangocon/rss?page=1&pagelen=100"
        url = self.feed.get_page_url(page_start=1, page_max=100)
        self.assertEqual(url, expected)

    def test_get_item_data(self):
        items = self.feed.get_response_items(self.response)
        data = self.feed.get_item_data(items[1])
        self.assertEqual(data, DISQUS_DATA)

    def test_get_response_items(self):
        videos = self.feed.get_response_items(self.response)
        self.assertEqual(len(videos), 77)


class BlipSearchTestCase(BlipTestCase):
    def setUp(self):
        BlipTestCase.setUp(self)
        search_file = self.get_data_file('blip/search.rss')
        self.response = feedparser.parse(search_file.read())
        self.search = self.suite.get_search('search query')

    def test_get_item_data(self):
        results = self.search.get_response_items(self.response)
        self.assertTrue(len(results) > 0)
        data = self.search.get_item_data(results[1])
        self.assertEqual(data, DISQUS_DATA)

    def test_unhandled_searches(self):
        self.assertRaises(UnhandledSearch,
                          self.suite.get_search,
                          'search query',
                          order_by='latest')


class BlipSuiteTestCase(BlipTestCase):
    def test_mp4_not_included(self):
        self.assertFalse(self.suite.handles_video_url(
                'http://blip.tv/file/get/Miropcf-Miro20Introduction119.mp4'))
