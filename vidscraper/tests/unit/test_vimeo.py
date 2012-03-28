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
import urlparse

from vidscraper.compat import json
from vidscraper.errors import VideoDeleted
from vidscraper.suites.vimeo import VimeoSuite, LAST_URL_CACHE


class VimeoTestCase(unittest.TestCase):
    def setUp(self):
        self.suite = VimeoSuite()
        self.base_url = "http://vimeo.com/2"
        self.video = self.suite.get_video(self.base_url)

    @property
    def data_file_dir(self):
        if not hasattr(self, '_data_file_dir'):
            test_dir = os.path.abspath(os.path.dirname(
                                                os.path.dirname(__file__)))
            self._data_file_dir = os.path.join(test_dir, 'data', 'vimeo')
        return self._data_file_dir

class VimeoSuiteTestCase(VimeoTestCase):
    def test_available_fields(self):
        self.assertEqual(
            self.suite.available_fields,
            set(['embed_code', 'description', 'flash_enclosure_url',
                 'user_url', 'publish_datetime', 'file_url_mimetype', 'title',
                 'file_url', 'thumbnail_url', 'link',
                 'user', 'guid', 'tags', 'file_url_expires']))

class VimeoOembedTestCase(VimeoTestCase):
    def test_get_oembed_url(self):
        url = self.suite.get_oembed_url(self.video)
        self.assertEqual(url, "http://vimeo.com/api/oembed.json?url=http%3A%2F%2Fvimeo.com%2F2")

    def test_parse_oembed_response(self):
        oembed_file = open(os.path.join(self.data_file_dir, 'oembed.json'))
        data = self.suite.parse_oembed_response(oembed_file.read())
        self.assertTrue(isinstance(data, dict))
        self.assertEqual(set(data), self.suite.oembed_fields)
        expected_data = {
            'embed_code': u'<iframe src="http://player.vimeo.com/video/2" '
                           'width="320" height="240" frameborder="0" '
                           'webkitAllowFullScreen allowFullScreen></iframe>',
            'user_url': u'http://vimeo.com/jakob',
            'thumbnail_url': u'http://b.vimeocdn.com/ts/228/979/22897998_200.jpg',
            'user': u'Jake Lodwick',
            'title': u'Good morning, universe'
        }
        for key in expected_data:
            self.assertTrue(key in data)
            self.assertEqual(data[key], expected_data[key])

    
class VimeoApiTestCase(VimeoTestCase):
    def test_get_api_url(self):
        api_url = self.suite.get_api_url(self.video)
        self.assertEqual(api_url, 'http://vimeo.com/api/v2/video/2.json')

    def test_parse_api_response(self):
        api_file = open(os.path.join(self.data_file_dir, 'api.json'))
        data = self.suite.parse_api_response(api_file.read())
        self.assertTrue(isinstance(data, dict))
        self.assertEqual(set(data), self.suite.api_fields)
        expected_data = {
            'thumbnail_url': u'http://b.vimeocdn.com/ts/228/979/22897998_200.jpg',
            'link': u'http://vimeo.com/2',
            'description': u'I shot this myself!',
            'title': u'Good morning, universe',
            'publish_datetime': datetime.datetime(2005, 2, 16, 23, 9, 19),
            'user_url': u'http://vimeo.com/jakob',
            'tags': [u'morning', u'bed', u'slow', u'my bedroom', u'creepy',
                     u'smile', u'fart'],
            'user': u'Jake Lodwick',
            'flash_enclosure_url': "http://vimeo.com/moogaloop.swf?clip_id=2",
            'guid': u'tag:vimeo,2005-02-16:clip2',
            'embed_code': u'<iframe src="http://player.vimeo.com/video/2" '
                           'width="320" height="240" frameborder="0" '
                           'webkitAllowFullScreen allowFullScreen></iframe>',
        }
        self.assertEqual(data, expected_data)

class VimeoScrapeTestCase(VimeoTestCase):
    def get_scrape_url(self):
        scrape_url = self.suite.get_scrape_url(self.video)
        self.assertEqual(scrape_url, 'http://vimeo.com/moogaloop/load/clip:2')

    def test_parse_scrape_response(self):
        scrape_file = open(os.path.join(self.data_file_dir, 'scrape.xml'))
        data = self.suite.parse_scrape_response(scrape_file.read())
        self.assertTrue(isinstance(data, dict))
        self.assertEqual(set(data), self.suite.scrape_fields)
        expected_data = {
            'title': u'Good morning, universe',
            'thumbnail_url': u'http://b.vimeocdn.com/ts/228/979/22897998_640.jpg',
            'link': u'http://vimeo.com/2',
            'user': u'Jake Lodwick',
            'user_url': u'http://vimeo.com/jakob',
            'embed_code': '<object width="400" height="300"><param name="allowfullscreen" value="true" /><param name="allowscriptaccess" value="always" /><param name="movie" value="http://vimeo.com/moogaloop.swf?clip_id=2&amp;server=vimeo.com&amp;show_title=1&amp;show_byline=1&amp;show_portrait=1&amp;color=00adef&amp;fullscreen=1&amp;autoplay=0&amp;loop=0" /><embed src="http://vimeo.com/moogaloop.swf?clip_id=2&amp;server=vimeo.com&amp;show_title=1&amp;show_byline=1&amp;show_portrait=1&amp;color=00adef&amp;fullscreen=1&amp;autoplay=0&amp;loop=0" type="application/x-shockwave-flash" allowfullscreen="true" allowscriptaccess="always" width="400" height="300"></embed></object><p><a href="http://vimeo.com/2">Good morning, universe</a> from <a href="http://vimeo.com/jakob">Jake Lodwick</a> on <a href="http://vimeo.com">Vimeo</a>.</p>',
            'file_url_expires': datetime.datetime(2011, 11, 29, 19, 11, 40),
            'file_url_mimetype': u'video/x-flv',
            'file_url': 'http://www.vimeo.com/moogaloop/play/clip:2/e82cb5d075e82a8cd790a1710e8b1d2f/1322593900/?q=sd'
        }
        for key in data:
            self.assertEqual(data[key], expected_data[key])

    def test_parse_scrape_response_noembed(self):
        scrape_file = open(os.path.join(self.data_file_dir, 'scrape_noembed.xml'))
        data = self.suite.parse_scrape_response(scrape_file.read())
        self.assertEqual(data, {
                'is_embedable': False})

class VimeoFeedTestCase(VimeoTestCase):
    def setUp(self):
        VimeoTestCase.setUp(self)
        feed_file = open(os.path.join(self.data_file_dir, 'feed.json'))
        response = json.loads(feed_file.read())
        self.feed = self.suite.get_feed('http://vimeo.com/jakob/videos/rss')
        self.feed._first_response = response
        self.entries = self.suite.get_feed_entries(self.feed, response)
        info_file = open(os.path.join(self.data_file_dir, 'info.json'))
        self.info_response = json.load(info_file)

    def test_get_feed_url(self):
        self.assertEqual(
            self.suite.get_feed_url('http://vimeo.com/jakob/videos/rss'),
            'http://vimeo.com/api/v2/jakob/videos.json')
        self.assertEqual(
            self.suite.get_feed_url(
                'http://vimeo.com/channels/whitehouse/videos/rss'),
            'http://vimeo.com/api/v2/channel/whitehouse/videos.json')
        self.assertEqual(
            self.suite.get_feed_url('http://vimeo.com/jakob/videos'),
            'http://vimeo.com/api/v2/jakob/videos.json')
        self.assertEqual(
            self.suite.get_feed_url('http://vimeo.com/jakob'),
            'http://vimeo.com/api/v2/jakob/videos.json')
        self.assertEqual(
            self.suite.get_feed_url(
                'http://vimeo.com/api/v2/jakob/videos.json'),
            'http://vimeo.com/api/v2/jakob/videos.json')

    def test_get_feed_title(self):
        self.assertEqual(
            self.suite.get_feed_title(self.feed, self.info_response),
            "Jake Lodwick's videos on Vimeo")

    def test_get_feed_title_likes(self):
        self.feed.url = self.feed.url.replace('videos.json', 'likes.json')
        self.assertEqual(
            self.suite.get_feed_title(self.feed, self.info_response),
            "Videos Jake Lodwick likes on Vimeo")        

    def test_get_feed_entry_count(self):
        self.assertEqual(
            self.suite.get_feed_entry_count(self.feed, self.info_response),
            359)

    def test_get_feed_entry_count_likes(self):
        self.feed.url = self.feed.url.replace('videos.json', 'likes.json')
        self.assertEqual(
            self.suite.get_feed_entry_count(self.feed, self.info_response),
            1333)        

    def test_get_feed_description(self):
        self.assertEqual(
            self.suite.get_feed_description(self.feed, self.info_response),
            "")

    def test_get_feed_webpage(self):
        self.assertEqual(
            self.suite.get_feed_webpage(self.feed, self.info_response),
            "http://vimeo.com/jakob/videos")

    def test_feed_webpage_likes(self):
        self.feed.url = self.feed.url.replace('videos.json', 'likes.json')
        self.assertEqual(
            self.suite.get_feed_webpage(self.feed, self.info_response),
            "http://vimeo.com/jakob/likes")

    def test_get_feed_thumbnail_url(self):
        self.assertEqual(
            self.suite.get_feed_thumbnail_url(self.feed, self.info_response),
            "http://b.vimeocdn.com/ps/137/734/1377340_300.jpg")

    def test_get_feed_guid(self):
        self.assertEqual(
            self.suite.get_feed_guid(self.feed, self.info_response),
            None)

    def test_get_feed_last_modified(self):
        self.assertEqual(
            self.suite.get_feed_last_modified(self.feed, self.info_response),
            None)

    def test_get_feed_etag(self):
        self.assertEqual(
            self.suite.get_feed_etag(self.feed, self.info_response),
            None)

    def test_parse_feed_entry_0(self):
        data = self.suite.parse_feed_entry(self.entries[0])
        self.assertTrue(isinstance(data, dict))
        expected_data = {
            'title': u'Grandfather recollects end of WWII',
            'embed_code': u'<iframe src="http://player.vimeo.com/video/'
                          u'24714980" width="320" height="240" frameborder="0" '
                          u'webkitAllowFullScreen allowFullScreen></iframe>',
            'publish_datetime': datetime.datetime(2011, 6, 6, 6, 45, 32),
            'link': u'http://vimeo.com/24714980',
            'description': '',
            'flash_enclosure_url': u"http://vimeo.com/moogaloop.swf?clip_id=24714980",
            'user': u"Jake Lodwick",
            'user_url': u"http://vimeo.com/jakob",
            "tags": [],
            'guid': u'tag:vimeo,2011-06-06:clip24714980',
            'thumbnail_url': u'http://b.vimeocdn.com/ts/162/178/162178490_200.jpg',
        }
        self.assertEqual(data, expected_data)

    def test_parse_feed_entry_1(self):
        data = self.suite.parse_feed_entry(self.entries[1])
        self.assertTrue(isinstance(data, dict))
        expected_data = {
            'link': u"http://vimeo.com/23833511",
            'title': u"Santa vs. The Easter Bunny",
            'description': u'A pre-Jackass prank and one of my first '
                            'edited-on-a-computer videos.<br />\n<br />\nShot '
                            'on December 23rd, 1999 as Towson Town Center, '
                            'Maryland, USA.<br />\n<br />\nJake Lodwick as '
                            'Santa<br />\nMatt Cockey as The Easter Bunny'
                            '<br />\n<br />\nShot by Ryan Welch, Tim Donahue, '
                            'and Will Cockey.<br />\nEscape driver: Wilson '
                            'Taliaferro.',
            'publish_datetime': datetime.datetime(2011, 5, 16, 20, 1, 30),
            'user': u"Jake Lodwick",
            'user_url': u"http://vimeo.com/jakob",
            'thumbnail_url': u"http://b.vimeocdn.com/ts/155/495/155495891_200.jpg",
            'flash_enclosure_url': u"http://vimeo.com/moogaloop.swf?clip_id=23833511",
            'tags': [u'archives', u'santa', u'easter bunny'],
            'guid': u'tag:vimeo,2011-05-16:clip23833511',
            'embed_code': u'<iframe src="http://player.vimeo.com/video/23833511" width="320" height="240" frameborder="0" webkitAllowFullScreen allowFullScreen></iframe>',
        }
        self.maxDiff = None
        self.assertEqual(data, expected_data)

    def test_next_feed_url(self):
        self.feed.url = "http://vimeo.com/nothing/here/?page=1"
        next_url = self.suite.get_next_feed_page_url(self.feed, None)
        self.assertEqual(next_url, "http://vimeo.com/nothing/here/?page=2")

        delattr(self.feed, LAST_URL_CACHE)
        self.feed.url = "http://vimeo.com/nothing/here/"
        next_url = self.suite.get_next_feed_page_url(self.feed, None)
        self.assertEqual(next_url, "http://vimeo.com/nothing/here/?page=2")

        delattr(self.feed, LAST_URL_CACHE)
        self.feed.url = "http://vimeo.com/nothing/here/?page=notanumber"
        next_url = self.suite.get_next_feed_page_url(self.feed, None)
        self.assertEqual(next_url, "http://vimeo.com/nothing/here/?page=2")


class VimeoSearchTestCase(VimeoTestCase):
    def setUp(self):
        VimeoTestCase.setUp(self)
        search_file = open(os.path.join(self.data_file_dir, 'search.json'))
        response = json.loads(search_file.read())
        self.search = self.suite.get_search(
            'search query',
            api_keys={'vimeo_key': 'BLANK',
                      'vimeo_secret': 'BLANK'})
        self.results = self.suite.get_search_results(self.search, response)

    def test_parse_search_result_1(self):
        data = self.suite.parse_search_result(self.search, self.results[0])
        self.assertTrue(isinstance(data, dict))
        expected_data = {
            'title': u'Dancing Pigeons - Ritalin',
            'link': 'http://vimeo.com/13639493',
            'description': u"""Directed by Tomas Mankovsky\n\nCast/ Performers (in order of appearance)\n\t\t\nOld Man -                           Keith Francis\nFlame Man - \t                     Adam Speers\nIce Man -\t                             Phil Zimmerman\n\t\nProducer\t  -                           Patrick Craig\n\t\nCasting Director -               \t     Sophie North\n\t\nEditor\t    -                         Julian Tranquille\n\t\nPost Production Supervisor\t -    Justin Brukman\n\t\n1st AD\t                          -   Chris Kelly\n1st AD\t                           -  Ben Fogg\nProduction Manager\t            - Adam Shaw\n\t\nDirector Of Photography\t     - Adam Frisch\nFocus Puller\t                     - Jeremy Fusco\nPhantom Technician\t            -  John Hadfield\nCamera Assistant\t            - Roland Philip\n7D Camera Assistant\t            - Chris Nunn\nGaffer\t                            - Tony Miller\nSpark\t                            - Jim Okeffe\nSpark\t                            - Chris Georgeous\nSpark\t                            - Jason Fletcher\nGenny Op\t                            - Kevin Cooli\nGenny Op\t                            - Lee Parfit\n\t\nArt Director\t                    - Arthur De Borman\nArt Director                            - Sam Ludgate\n\t\nSpecial Effects\t         -            Artem\nSpecial Effects Supervisor\t-     Simon Tayler\nSpecial Effects Technicians\t -    Toby Stewart\nSpecial Effects Technicians\t  -   Jonathan Bickerdike\nSpecial Effects Technicians\t   -  Matt Loader\n\t\nHair & Make Up\t                  -   Izzy Broad\nStylist\t                          -   Tess Loe\nStylist Assistant\t                   -  Daisy Babbington \n\t\nFire Cover\t                           -  1st Defense\nMedical Cover\t                   -  Location Medical\nAnimals\t                            - A-Z Animals - Gerry Cott\n\t\nPhotography\t                    - Marcus Palmqvist\nPhotography Assistant\t            - Belinda Foord\n\t\nProduction Assistant\t           -  Rob Leonard\nRunner\t                            - Sophia Marks\nRunner\t                            - Lola Marks\nRunner\t                            - Anna Fogg\n\t\nSpecial Thanks To\t             \n\nCut and Run\n\t                                     Take 2 Films\n\t                                     MPC\n\t                                     Green Door Films\n\t                                     Panalux\n\t                                     Black Country Parks\n\t                                     San Remo Caf\xe9\n\nCommissioned by Diesel:U:Music""",
            'thumbnail_url': 'http://b.vimeocdn.com/ts/786/198/78619855_200.jpg',
            'user': 'Blink',
            'user_url': 'http://vimeo.com/user4230856',
            'publish_datetime': datetime.datetime(2010, 07, 26, 4, 29, 33),
            'tags': ['Dancing Pigeons', 'Ritalin', 'Tomas Mankovsky', 'Blink',
                     'Music Video', 'flamethrower', 'fire extinguisher'],
            'flash_enclosure_url': 'http://vimeo.com/moogaloop.swf?clip_id=13639493',
            'embed_code': """<iframe src="http://player.vimeo.com/video/\
13639493" width="320" height="240" frameborder="0" webkitAllowFullScreen \
allowFullScreen></iframe>"""
        }
        for key in expected_data:
            self.assertTrue(key in data)
            self.assertEqual(data[key], expected_data[key])

    def test_get_search_with_deleted_video(self):
        search_file = open(os.path.join(self.data_file_dir,
                                        'search_with_deleted.json'))
        response = json.loads(search_file.read())
        search = self.suite.get_search(
            'search query',
            api_keys={'vimeo_key': 'BLANK',
                      'vimeo_secret': 'BLANK'})
        results = self.suite.get_search_results(search, response)
        self.assertEqual(len(results), 50)
        self.assertRaises(VideoDeleted,
                          self.suite.parse_search_result,
                          search, results[49])

    def test_get_search_url(self):
        extra_params = {'bar': 'baz'}
        self.assertEqual(
            self.suite.get_search_url(self.search,
                                      extra_params=extra_params),
            'http://vimeo.com/api/rest/v2/?bar=baz&full_response=1&format=json'
            '&query=query+search&api_key=BLANK&method=vimeo.videos.search')
        self.search.order_by = 'relevant'
        self.assertEqual(
            self.suite.get_search_url(self.search),
            'http://vimeo.com/api/rest/v2/?sort=relevant&full_response=1&'
            'format=json&query=query+search&api_key=BLANK&'
            'method=vimeo.videos.search')
        self.search.order_by = 'latest'
        self.assertEqual(
            self.suite.get_search_url(self.search),
            'http://vimeo.com/api/rest/v2/?sort=newest&full_response=1&'
            'format=json&query=query+search&api_key=BLANK&'
            'method=vimeo.videos.search')

    def test_next_page_url(self):
        response = {'videos': {'total': '10', 'page': '1', 'perpage': '50'}}
        new_url = self.suite.get_next_search_page_url(self.search,
                                                      response)
        self.assertTrue(new_url is None)
        response['videos']['total'] = '100'
        new_url = self.suite.get_next_search_page_url(self.search,
                                                      response)
        self.assertFalse(new_url is None)
        parsed = urlparse.urlparse(new_url)
        params = urlparse.parse_qs(parsed.query)
        self.assertEqual(int(params['page'][0]), 2)
