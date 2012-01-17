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
import urllib
import urlparse

from vidscraper.errors import CantIdentifyUrl
from vidscraper.suites import Video
from vidscraper.suites.blip import BlipSuite


class BlipTestCase(unittest.TestCase):
    def setUp(self):
        self.suite = BlipSuite()

    @property
    def data_file_dir(self):
        if not hasattr(self, '_data_file_dir'):
            test_dir = os.path.abspath(os.path.dirname(
                                                os.path.dirname(__file__)))
            self._data_file_dir = os.path.join(test_dir, 'data', 'blip')
        return self._data_file_dir

    def _check_disqus_data(self, data):
        """Check that data for a specific post is parsed as expected."""
        self.assertEqual(data['guid'], u'4809E60A-C2AB-11DF-BBAC-A6337D0214E0')
        self.assertEqual(data['link'], "http://blip.tv/file/4135225")
        self.assertEqual(data['title'],
                        "Scaling the World's Largest Django Application")
        self.assertEqual(data['description'],
                        "<p>Disqus, one of the largest Django applications in "
                        "the world, will explain how they deal with scaling "
                        "complexities in a small startup.</p>")
        self.assertEqual(data['file_url'], "http://blip.tv/file/get/Robertlofthouse-ScalingTheWorldsLargestDjangoApplication558.ogv")
        self.assertEqual(data['embed_code'],
                        '<embed src="http://blip.tv/play/AYH9xikC" '
                        'type="application/x-shockwave-flash" width="480" '
                        'height="390" wmode="transparent" '
                        'allowscriptaccess="always" allowfullscreen="true" >'
                        '</embed>')
        self.assertEqual(data['publish_datetime'],
                         datetime.datetime(2010, 9, 17, 22, 31, 14))
        self.assertEqual(data['thumbnail_url'],
                        "http://a.images.blip.tv/Robertlofthouse-ScalingTheWorldsLargestDjangoApplication538.png")
        self.assertEqual(data['tags'],
                        [u'shmpe', u'djangocon', u'2010'])
        self.assertEqual(data['user'], 'djangocon')
        self.assertEqual(data['user_url'], 'http://djangocon.blip.tv/')
        self.assertEqual(data['license'],
                         'http://creativecommons.org/licenses/by-nc-sa/3.0/')
        


class BlipApiTestCase(BlipTestCase):
    def setUp(self):
        BlipTestCase.setUp(self)
        self.base_url = "http://blip.tv/djangocon/lightning-talks-day-1-4167881"
        self.video = self.suite.get_video(url=self.base_url)

    def _test_video_api_url(self, video):
        api_url = self.suite.get_api_url(video)
        parsed_url = urlparse.urlparse(api_url)
        self.assertEqual(parsed_url[2], "/rss/4167881")

    def test_get_api_url(self):
        self._test_video_api_url(self.video)

    def test_get_api_url_old_url(self):
        self.video.url = 'http://blip.tv/file/1077145/'
        api_url = self.suite.get_api_url(self.video)
        parsed_url = urlparse.urlparse(api_url)
        self.assertEqual(parsed_url[2], '/rss/1083325')

    def test_get_api_url_overrides(self):
        video = self.suite.get_video(url="%s?skin=json" % self.base_url)
        self._test_video_api_url(video)

    def test_parse_api_response(self):
        api_file = open(os.path.join(self.data_file_dir, 'api.rss'))
        data = self.suite.parse_api_response(api_file.read())
        self.assertTrue(isinstance(data, dict))
        self.assertEqual(set(data), self.suite.api_fields)
        self._check_disqus_data(data)


class BlipOembedTestCase(BlipTestCase):
    def setUp(self):
        BlipTestCase.setUp(self)
        self.base_url = "http://blip.tv/djangocon/lightning-talks-day-1-4167881"
        self.video = self.suite.get_video(url=self.base_url)

    def test_get_oembed_url(self):
        escaped_url = urllib.quote_plus(self.video.url)
        expected = "http://blip.tv/oembed/?url=%s" % escaped_url
        oembed_url = self.suite.get_oembed_url(self.video)
        self.assertEqual(oembed_url, expected)

    def test_parse_oembed_response(self):
        oembed_file = open(os.path.join(
                            self.data_file_dir, 'oembed.json'))
        data = self.suite.parse_oembed_response(oembed_file.read())
        self.assertTrue(isinstance(data, dict))
        self.assertEqual(set(data), self.suite.oembed_fields)
        self._check_disqus_data(data)

    def _check_disqus_data(self, data):
        """
        OEmbed doesn't return as much data - and what it does return is ever so
        slightly different.

        """
        self.assertEqual(data['title'],
                        "Scaling the World's Largest Django Application")
        self.assertEqual(data['embed_code'],
                        '<iframe src="http://blip.tv/play/AYH9xikC.html" '
                        'width="640" height="510" frameborder="0" '
                        'allowfullscreen></iframe><embed '
                        'type="application/x-shockwave-flash" '
                        'src="http://a.blip.tv/api.swf#AYH9xikC" '
                        'style="display:none"></embed>')
        self.assertEqual(data['thumbnail_url'],
                        "http://a.images.blip.tv/Robertlofthouse-ScalingTheWorldsLargestDjangoApplication538.png")
        self.assertEqual(data['user'], 'djangocon')
        self.assertEqual(data['user_url'], 'http://blip.tv/djangocon')


class BlipFeedTestCase(BlipTestCase):
    def setUp(self):
        BlipTestCase.setUp(self)
        self.feed_url = 'http://blip.tv/djangocon'
        self.feed = self.suite.get_feed(self.feed_url)
        self.feed_data = open(
            os.path.join(self.data_file_dir, 'feed.rss')
            ).read()
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
        self.assertTrue(len(entries), 77)

    def test_parse_entry(self):
        response = self.suite.get_feed_response(self.feed, self.feed_data)
        entries = self.suite.get_feed_entries(self.feed, response)
        data = self.suite.parse_feed_entry(entries[1])
        self.assertTrue(isinstance(data, dict))
        self._check_disqus_data(data)

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
        self.feed_data = open(
            os.path.join(self.data_file_dir, 'search.rss')
        ).read()
        self.search = self.suite.get_search('search query')

    def test_parse_search_feed(self):
        response = self.suite.get_search_response(self.search, self.feed_data)
        results = self.suite.get_search_results(self.search, response)
        self.assertTrue(len(results) > 0)

    def test_parse_result(self):
        response = self.suite.get_search_response(self.search, self.feed_data)
        results = self.suite.get_search_results(self.search, response)
        data = self.suite.parse_search_result(self.search, results[1])
        self.assertTrue(isinstance(data, dict))
        self._check_disqus_data(data)

class BlipSuiteTestCase(BlipTestCase):
    def test_mp4_not_included(self):
        self.assertFalse(self.suite.handles_video_url(
                'http://blip.tv/file/get/Miropcf-Miro20Introduction119.mp4'))
