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

import mock
import unittest2

from vidscraper.exceptions import VideoDeleted
from vidscraper.suites.vimeo import (oauth_hook, Suite,
                                     SimpleLoader, SimpleFeed,
                                     AdvancedLoader, AdvancedFeed)
from vidscraper.tests.base import BaseTestCase


class VimeoTestCase(BaseTestCase):
    def setUp(self):
        self.suite = Suite()


class SuiteTestCase(VimeoTestCase):
    def test_available_fields(self):
        self.assertEqual(
            self.suite.available_fields,
            set(['embed_code', 'description', 'flash_enclosure_url',
                 'user_url', 'publish_datetime', 'title',
                 'thumbnail_url', 'link',
                 'user', 'guid', 'tags',]))

    
class SimpleLoaderTestCase(VimeoTestCase):
    def setUp(self):
        super(SimpleLoaderTestCase, self).setUp()
        self.loader = SimpleLoader("http://vimeo.com/2")

    def test_get_url(self):
        api_url = self.loader.get_url()
        self.assertEqual(api_url, 'http://vimeo.com/api/v2/video/2.json')

    def test_get_video_data(self):
        expected_data = {
            'thumbnail_url': u'http://b.vimeocdn.com/ts/228/979/22897998_640.jpg',
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
        }
        api_file = self.get_data_file('vimeo/simple.json')
        response = self.get_response(api_file.read())
        data = self.loader.get_video_data(response)
        self.assertEqual(set(data), self.loader.fields)
        self.assertDictEqual(data, expected_data)


@unittest2.skipIf(oauth_hook is None, "Advanced api requires requests-oauth")
class VimeoAdvancedLoaderTestCase(VimeoTestCase):
    def setUp(self):
        super(VimeoAdvancedLoaderTestCase, self).setUp()
        self.loader = AdvancedLoader("http://vimeo.com/2",
                                     api_keys={'vimeo_key': 'BLANK',
                                               'vimeo_secret': 'BLANK'})

    def test_get_url(self):
        api_url = self.loader.get_url()
        self.assertEqual(api_url, 'http://vimeo.com/api/rest/v2?format=json&'
                                  'full_response=1&method=vimeo.videos.'
                                  'getInfo&video_id=2')

    def test_get_video_data(self):
        expected_data = {
            'thumbnail_url': u'http://b.vimeocdn.com/ts/228/979/22897998_640.jpg',
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
        }
        api_file = self.get_data_file('vimeo/advanced.json')
        response = self.get_response(api_file.read())
        data = self.loader.get_video_data(response)
        self.assertEqual(set(data), self.loader.fields)
        self.assertDictEqual(data, expected_data)


class SimpleFeedTestCase(VimeoTestCase):
    """
    Tests the feed if no API keys are supplied.
    """
    def setUp(self):
        VimeoTestCase.setUp(self)
        self.feed = self.suite.get_feed('http://vimeo.com/jakob/videos/rss')

    def test_is_simple(self):
        self.assertTrue(isinstance(self.feed, SimpleFeed))

    def test_feed_urls(self):
        valid_feed_inputs = (
            (('/plasticcut',),
             {'user_id': 'plasticcut'}),

            (('/plasticcut/videos',
              '/plasticcut/videos/rss',
              '/plasticcut/videos/sort:oldest',
              '/plasticcut/videos/sort:oldest/format:thumbnail'),
             {'user_id': 'plasticcut',
              'request_type': 'videos'}),

            (('/plasticcut/likes',
              '/plasticcut/likes/rss',
              '/plasticcut/likes/sort:oldest',
              '/plasticcut/likes/sort:oldest/format:thumbnail'),
              {'user_id': 'plasticcut',
               'request_type': 'likes'}),

            (('/channels/deutschekurze',
              '/channels/deutschekurze/videos/rss'),
             {'channel_id': 'deutschekurze'}),

            (('/groups/markenfaktor',
              '/groups/markenfaktor/videos',
              '/groups/markenfaktor/videos/sort:oldest',
              '/groups/markenfaktor/videos/sort:oldest/format:thumbnail'),
             {'group_id': 'markenfaktor'}),

            (('/album/82090',
              '/album/82090/format:thumbnail'),
             {'album_id': '82090'}),

            (('/api/v2/album/82090/videos.json',),
             {'album_id': '82090',
              'request_type': 'videos'}),
            (('/api/v2/channel/deutschekurze/videos.json',),
             {'channel_id': 'deutschekurze',
              'request_type': 'videos'}),
            (('/api/v2/group/markenfaktor/videos.json',),
             {'group_id': 'markenfaktor',
              'request_type': 'videos'}),
            (('/api/v2/plasticcut/videos.json',),
             {'user_id': 'plasticcut',
              'request_type': 'videos'}),
        )

        for scheme in ("http", "https"):
            for netloc in ("vimeo.com", "www.vimeo.com"):
                for paths, expected in valid_feed_inputs:
                    for path in paths:
                        data = self.feed.get_url_data("{0}://{1}{2}".format(
                                    scheme, netloc, path))
                        data = dict((k, v) for k, v in data.items()
                                    if v is not None)
                        self.assertEqual(data, expected)

    def test_data_from_response__user(self):
        info_file = self.get_data_file('vimeo/info_user.json')
        response = self.get_response(info_file.read())
        expected = {
            'title': "Jake Lodwick's videos",
            'video_count': 60,
            'description': '',
            'webpage': u'http://vimeo.com/jakob/videos',
            'thumbnail_url': "http://b.vimeocdn.com/ps/137/734/1377340_300.jpg",
        }
        data = self.feed.data_from_response(response)
        self.assertEqual(data, expected)

        self.feed.url_data['request_type'] = 'likes'
        expected.update({
            'title': "Videos Jake Lodwick likes",
            'webpage': u'http://vimeo.com/jakob/likes',
        })
        data = self.feed.data_from_response(response)
        self.assertEqual(data, expected)

        self.feed.url_data['request_type'] = 'appears_in'
        expected.update({
            'title': "Videos Jake Lodwick appears in",
            'webpage': u'http://vimeo.com/jakob',
        })
        data = self.feed.data_from_response(response)
        self.assertEqual(data, expected)

        self.feed.url_data['request_type'] = 'all_videos'
        expected.update({
            'title': "Jake Lodwick's videos and videos Jake Lodwick appears in",
            'video_count': None,
        })
        data = self.feed.data_from_response(response)
        self.assertEqual(data, expected)

        self.feed.url_data['request_type'] = 'subscriptions'
        expected.update({
            'title': "Videos Jake Lodwick is subscribed to",
        })
        data = self.feed.data_from_response(response)
        self.assertEqual(data, expected)

    def test_data_from_response__album(self):
        info_file = self.get_data_file('vimeo/info_album.json')
        response = self.get_response(info_file.read())
        expected = {
            'webpage': u'http://vimeo.com/album/82090',
            'video_count': 7,
            'thumbnail_url': None,
            'description': u'',
            'title': u'Plastic.Cut'
        }
        data = self.feed.data_from_response(response)
        self.assertEqual(data, expected)

    def test_data_from_response__channel(self):
        info_file = self.get_data_file('vimeo/info_channel.json')
        response = self.get_response(info_file.read())
        expected = {
            'webpage': u'http://vimeo.com/channels/deutschekurze',
            'video_count': 22,
            'thumbnail_url': u'http://channelheader.vimeo.com.s3.amazonaws.com/654/65472_980.jpg',
            'description': u"Nur allerfeinste und handerlesene deutsche "
                           u"Kurzfilmware gibt es hier zu rezipieren. Und "
                           u"damit hier eben nur edelster Stoff angeboten "
                           u"werden kann, muss man sich schon bewerben: "
                           u"Entweder man wird Mitglied in der gleichnamigen "
                           u"Gruppe und postet dort sein Werk oder man "
                           u"verlinkt es weiter unten in der Shoutbox. Der "
                           u"Chef himself (Sascha Dornh\xf6fer) pr\xfcft die "
                           u"Ware kritisch und wenn's nach seinem "
                           u"supersubjektiven Gusto ist, wird man mit einer "
                           u"Ver\xf6ffentlichung geadelt. Nur fertige Werke "
                           u"kommen in die T\xfcte, gerne auch Musikvideos, "
                           u"die als eigenst\xe4ndiger Film funktionieren "
                           u"und wenn gesprochen wird, dann deutsch. Trailer "
                           u"oder Teaser haben hier nichts verloren.<br />\r"
                           u"\n<br />\r\n---<br />\r\n<br />\r\nMachen Sie "
                           u"sich zum angesehenen Mitglied der entsprechenden"
                           u" Gruppe:<br />\r\nvimeo.com/groups/deutschekurze"
                           u"<br />\r\n<br />\r\nShortcut zu diesem feinen "
                           u"Channel:<br />\r\n"
                           u"vimeo.com/channels/deutschekurze<br />\r\n<br />"
                           u"\r\nDeutsche Webserien gibts \xfcbrigens hier:"
                           u"<br />\r\nvimeo.com/groups/webserien<br />\r\n"
                           u"<br />\r\nOffizielle Website:<br />\r\n"
                           u"www.neuemassenproduktion.de",
            'title': u'Deutsche Kurzfilme'
        }
        data = self.feed.data_from_response(response)
        self.assertEqual(data, expected)

    def test_data_from_response__group(self):
        info_file = self.get_data_file('vimeo/info_group.json')
        response = self.get_response(info_file.read())
        expected = {
            'webpage': u'http://vimeo.com/groups/markenfaktor',
            'video_count': 60,
            'thumbnail_url': u'http://groupheader.vimeo.com.s3.amazonaws.com/389/38990_980.',
            'description': u'Der Fachblog f\xfcr Marke, Kommunikation und Des'
                           u'ign. <br />\r\n<br />\r\nmarkenfaktor ist auch h'
                           u'ier:<br />\r\n<br />\r\nwww.markenfaktor.de<br /'
                           u'>\r\nwww.facebook.com/\u200bmarkenfaktor<br />\r'
                           u'\nwww.plus.google.com/109380568776060074590/post'
                           u's<br />\r\nwww.twitter.com/\u200bmarkenfaktor<br'
                           u' />\r\nwww.pinterest.com/markenfaktor/<br />\r\n'
                           u'www.youtube.com/\u200buser/\u200bmarkenfaktor<br'
                           u' />\r\nwww.xing.com/\u200bnet/\u200bmarkenfaktor'
                           u'<br />\r\nwww.flickr.com/\u200bpeople/\u200bmark'
                           u'enfaktor<br />\r\nwww.soundcloud.com/\u200bmarke'
                           u'nfaktor/\u200bdropbox<br />\r\n<br />\r\nmarkenf'
                           u'aktor Magazin:<br />\r\nwww.paper.li/\u200bmarke'
                           u'nfaktor',
            'title': u'markenfaktor'
        }
        data = self.feed.data_from_response(response)
        self.assertEqual(data, expected)

    def test_get_video_data(self):
        feed_file = self.get_data_file('vimeo/feed.json')
        response = self.get_response(feed_file.read())
        items = self.feed.get_response_items(response)

        data = self.feed.get_video_data(items[0])
        expected = {
            'title': u'Grandfather recollects end of WWII',
            'publish_datetime': datetime.datetime(2011, 6, 6, 6, 45, 32),
            'link': u'http://vimeo.com/24714980',
            'description': '',
            'flash_enclosure_url': u"http://vimeo.com/moogaloop.swf?clip_id=24714980",
            'user': u"Jake Lodwick",
            'user_url': u"http://vimeo.com/jakob",
            "tags": [],
            'guid': u'tag:vimeo,2011-06-06:clip24714980',
            'thumbnail_url': u'http://b.vimeocdn.com/ts/162/178/162178490_640.jpg',
        }
        self.assertEqual(data, expected)

        data = self.feed.get_video_data(items[1])
        expected = {
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
            'thumbnail_url': u"http://b.vimeocdn.com/ts/155/495/155495891_640.jpg",
            'flash_enclosure_url': u"http://vimeo.com/moogaloop.swf?clip_id=23833511",
            'tags': [u'archives', u'santa', u'easter bunny'],
            'guid': u'tag:vimeo,2011-05-16:clip23833511',
        }
        self.assertEqual(data, expected)

    def test_get_page_url(self):
        expected = "http://vimeo.com/api/v2/jakob/videos.json?page=2"
        url = self.feed.get_page_url(page_start=21, page_max=20)
        self.assertEqual(url, expected)


@unittest2.skipIf(oauth_hook is None, "Advanced api requires requests-oauth")
class AdvancedFeedTestCase(VimeoTestCase):
    """
    Tests the feed if API keys are supplied.
    """
    def setUp(self):
        VimeoTestCase.setUp(self)
        self.feed = self.suite.get_feed('http://vimeo.com/plasticcut/videos',
                                        api_keys={'vimeo_key': 'BLANK',
                                                  'vimeo_secret': 'BLANK'})

    def test_is_advanced(self):
        self.assertTrue(isinstance(self.feed, AdvancedFeed))

    def test_get_response_items(self):
        feed_file = self.get_data_file('vimeo/feed_advanced.json')
        response = self.get_response(feed_file.read())
        items = self.feed.get_response_items(response)
        self.assertEqual(len(items), 46)

    def test_get_response_items__empty(self):
        """
        If the page has 0 videos on it, no response items should be returned.

        """
        response = mock.MagicMock(json={'videos': {'on_this_page': 0}})
        items = self.feed.get_response_items(response)
        self.assertEqual(len(items), 0)

    def test_get_response_items__no_videos(self):
        """
        If the page doesn't contain any videos at all, no response items
        should be returned.

        """
        response = mock.MagicMock(json={})
        items = self.feed.get_response_items(response)
        self.assertEqual(len(items), 0)

    def test_get_video_data(self):
        feed_file = self.get_data_file('vimeo/feed_advanced.json')
        response = self.get_response(feed_file.read())
        items = self.feed.get_response_items(response)

        data = self.feed.get_video_data(items[0])
        expected = {
            'description': '',
            'user_url': u'http://vimeo.com/plasticcut',
            'link': u'http://vimeo.com/39590925',
            'user': u'Plastic.Cut',
            'guid': u'tag:vimeo,2012-04-01:clip39590925',
            'flash_enclosure_url': u'http://vimeo.com/moogaloop.swf?clip_id=39590925',
            'title': u'Tula "Dragon" - March 30th, 2012 @ Franz Mehlhose, Erfurt (GER)',
            'tags': [u'Tula', u'Dragon', u'Franz Mehlhose', u'Erfurt',
                     u'Patrick Richter', u'Roman Hagenbrock'],
            'thumbnail_url': u'http://b.vimeocdn.com/ts/273/118/273118277_640.jpg',
            'publish_datetime': datetime.datetime(2012, 4, 1, 15, 49, 22)
        }
        self.assertEqual(data, expected)

    def test_data_from_response(self):
        feed_file = self.get_data_file('vimeo/feed_advanced.json')
        response = self.get_response(feed_file.read())
        data = self.feed.data_from_response(response)
        self.assertEqual(data, {'video_count': 46})

    def test_data_from_response__no_videos(self):
        """
        If the response doesn't contain any videos, no items should be
        returned.

        """
        response = mock.MagicMock(json={})
        data = self.feed.data_from_response(response)
        self.assertEqual(data, {'video_count': 0})

    def test_get_page_url(self):
        expected = ("http://vimeo.com/api/rest/v2?format=json&full_response=1"
                    "&per_page=50&method=vimeo.videos.getUploaded&"
                    "sort=newest&page=1&user_id=plasticcut")
        url = self.feed.get_page_url(page_start=21, page_max=20)
        self.assertEqual(url, expected)


@unittest2.skipIf(oauth_hook is None, "Advanced api requires requests-oauth")
class VimeoSearchTestCase(VimeoTestCase):
    def setUp(self):
        VimeoTestCase.setUp(self)
        self.search = self.suite.get_search(
            u'search query! \u65e5\u672c\u8a9e',
            api_keys={'vimeo_key': 'BLANK',
                      'vimeo_secret': 'BLANK'})

    def test_get_video_data(self):
        search_file = self.get_data_file('vimeo/search.json')
        response = self.get_response(search_file.read())
        results = self.search.get_response_items(response)
        data = self.search.get_video_data(results[0])
        expected_data = {
            'title': u'Dancing Pigeons - Ritalin',
            'link': 'http://vimeo.com/13639493',
            'description': u"""Directed by Tomas Mankovsky\n\nCast/ Performers (in order of appearance)\n\t\t\nOld Man -                           Keith Francis\nFlame Man - \t                     Adam Speers\nIce Man -\t                             Phil Zimmerman\n\t\nProducer\t  -                           Patrick Craig\n\t\nCasting Director -               \t     Sophie North\n\t\nEditor\t    -                         Julian Tranquille\n\t\nPost Production Supervisor\t -    Justin Brukman\n\t\n1st AD\t                          -   Chris Kelly\n1st AD\t                           -  Ben Fogg\nProduction Manager\t            - Adam Shaw\n\t\nDirector Of Photography\t     - Adam Frisch\nFocus Puller\t                     - Jeremy Fusco\nPhantom Technician\t            -  John Hadfield\nCamera Assistant\t            - Roland Philip\n7D Camera Assistant\t            - Chris Nunn\nGaffer\t                            - Tony Miller\nSpark\t                            - Jim Okeffe\nSpark\t                            - Chris Georgeous\nSpark\t                            - Jason Fletcher\nGenny Op\t                            - Kevin Cooli\nGenny Op\t                            - Lee Parfit\n\t\nArt Director\t                    - Arthur De Borman\nArt Director                            - Sam Ludgate\n\t\nSpecial Effects\t         -            Artem\nSpecial Effects Supervisor\t-     Simon Tayler\nSpecial Effects Technicians\t -    Toby Stewart\nSpecial Effects Technicians\t  -   Jonathan Bickerdike\nSpecial Effects Technicians\t   -  Matt Loader\n\t\nHair & Make Up\t                  -   Izzy Broad\nStylist\t                          -   Tess Loe\nStylist Assistant\t                   -  Daisy Babbington \n\t\nFire Cover\t                           -  1st Defense\nMedical Cover\t                   -  Location Medical\nAnimals\t                            - A-Z Animals - Gerry Cott\n\t\nPhotography\t                    - Marcus Palmqvist\nPhotography Assistant\t            - Belinda Foord\n\t\nProduction Assistant\t           -  Rob Leonard\nRunner\t                            - Sophia Marks\nRunner\t                            - Lola Marks\nRunner\t                            - Anna Fogg\n\t\nSpecial Thanks To\t             \n\nCut and Run\n\t                                     Take 2 Films\n\t                                     MPC\n\t                                     Green Door Films\n\t                                     Panalux\n\t                                     Black Country Parks\n\t                                     San Remo Caf\xe9\n\nCommissioned by Diesel:U:Music""",
            'thumbnail_url': 'http://b.vimeocdn.com/ts/786/198/78619855_640.jpg',
            'user': 'Blink',
            'user_url': 'http://vimeo.com/user4230856',
            'publish_datetime': datetime.datetime(2010, 07, 26, 4, 29, 33),
            'tags': ['Dancing Pigeons', 'Ritalin', 'Tomas Mankovsky', 'Blink',
                     'Music Video', 'flamethrower', 'fire extinguisher'],
            'flash_enclosure_url': 'http://vimeo.com/moogaloop.swf?clip_id=13639493',
            'guid': u'tag:vimeo,2010-07-26:clip13639493',
        }
        self.assertDictEqual(data, expected_data)

    def test_get_search_with_deleted_video(self):
        search_file = self.get_data_file('vimeo/search_with_deleted.json')
        response = self.get_response(search_file.read())
        results = self.search.get_response_items(response)

        # Try this to be sure it doesn't error.
        self.search.get_video_data(results[0])

        self.assertEqual(len(results), 50)
        self.assertRaises(VideoDeleted,
                          self.search.get_video_data,
                          results[49])

    def test_get_page_url(self):
        expected = ("http://vimeo.com/api/rest/v2?format=json&full_response=1"
                    "&per_page=50&method=vimeo.videos.search&sort=relevant"
                    "&page=2&query=search+query%21+%E6%97%A5%E6%9C%AC%E8%AA%9E")
        url = self.search.get_page_url(page_start=57, page_max=50)
        self.assertEqual(url, expected)
