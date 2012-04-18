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
import json
import urllib
import urllib2
import urlparse

import feedparser
import requests

from vidscraper.exceptions import UnhandledURL
from vidscraper.suites.youtube import (YouTubeSuite, YouTubeApiLoader,
                                       YouTubeScrapeLoader,
                                       YouTubeOEmbedLoader,
                                       YouTubePathMixin)
from vidscraper.tests.base import BaseTestCase


CARAMELL_DANSEN_API_DATA = {
    'link': u'http://www.youtube.com/watch?v=J_DV9b0x7v4',
    'title': u'CaramellDansen (Full Version + Lyrics)',
    'description': u'English:\ndo-do-do-oo, yeah-yeah-yeah-yeah\n\nWe wonder are you ready to join us now\nhands in the air\nwe will show you how\ncome and try\ncaramell will be your guide\n\nSo come and move your hips sing wha-a-a\nlook at hips, do it La-la-la\nyou and me can sing this melody\n\nOh-wa-a-a-a\nDance to the beat\nWave your hands together\nCome feel the heat forever and forever\nListen and learn it is time for prancing\nNow we are here with caramel dancing\n\nO-o-oa-oa\nO-o-oa-oa-a-a\nO-o-oa-oa\nO-o-oa-oa-a-a\n\nFrom Sweden to UK we will bring our song, Australia, USA and people of Hong Kong.\nThey have heard this meaning all around the world\n\nSo come and move your hips sing wha-a-a\nLook at your hips, do it La-la-la\nYou and me can sing this melody\n\nSo come and dance to the beat\nWave your hands together\nCome feel the heat forever and forever\nListen and learn it is time for prancing\nNow we are here with caramel dancing\n\n(Dance to the beat\nwave your hands together\ncome feel the heat forever and forever\nlisten and learn it is time for prancing\nnow we are here with caramel dancing)\n\nU-u-ua-ua\nU-u-ua-ua-a-a\nU-u-ua-ua\nU-u-ua-ua-a-a\n\nSo come and dance to the beat\nWave your hands together\nCome feel the heat forever and forever\nListen and learn it is time for prancing\nNow we are here with caramel dancing...\nDance to the beat\nWave your hands together\nCome feel the heat forever and forever\nListen and learn it is time for prancing\nNow we are here with caramel dancing \n\nSwedish:\nVi undrar \xe4r ni redo att vara med\nArmarna upp nu ska ni f\xe5 se\nKom igen\nVem som helst kan vara med\n\nS\xe5 r\xf6r p\xe5 era f\xf6tter\nOa-a-a\nOch vicka era h\xf6fter\nO-la-la-la\nG\xf6r som vi\nTill denna melodi\n\nDansa med oss\nKlappa era h\xe4nder\nG\xf6r som vi g\xf6r\nTa n\xe5gra steg \xe5t v\xe4nster\nLyssna och l\xe4r\nMissa inte chansen\nNu \xe4r vi h\xe4r med\nCaramelldansen\nO-o-oa-oa...\n\nDet blir en sensation \xf6verallt f\xf6rst\xe5s\nP\xe5 fester kommer alla att sl\xe4ppa loss\nKom igen\nNu tar vi stegen om igen\n\nS\xe5 r\xf6r p\xe5 era f\xf6tter\nOa-a-a\nOch vicka era h\xf6fter\nO-la-la-la\nG\xf6r som vi\nTill denna melodi\n\nS\xe5 kom och\nDansa med oss\nKlappa era h\xe4nder\nG\xf6r som vi g\xf6r\nTa n\xe5gra steg \xe5t v\xe4nster\nLyssna och l\xe4r\nMissa inte chansen\nNu \xe4r vi h\xe4r med\nCaramelldansen\n\nDansa med oss\nKlappa era h\xe4nder\nG\xf6r som vi g\xf6r\nTa n\xe5gra steg \xe5t v\xe4nster\nLyssna och l\xe4r\nMissa inte chansen\nNu \xe4r vi h\xe4r med\nCaramelldansen',
    'thumbnail_url': u'http://i.ytimg.com/vi/J_DV9b0x7v4/hqdefault.jpg',
    'user': u'DrunkenVuko',
    'user_url': u'http://www.youtube.com/user/DrunkenVuko',
    'flash_enclosure_url': u'http://www.youtube.com/watch?v=J_DV9b0x7v4&feature=youtube_gdata_player',
    'tags': set([
        u"caramell",
        u"dance",
        u"dansen",
        u"hip",
        u"hop",
        u"s\xfcchtig",
        u"geil",
        u"cool",
        u"lustig",
        u"manga",
        u"schweden",
        u"anime",
        u"musik",
        u"music",
        u"funny",
        u"caramelldansen",
        u"U-U-U-Aua",
        u"Music", # technically a category, but historically included
    ]),
    'publish_datetime': datetime.datetime(2007, 5, 7, 22, 15, 21),
    'guid': u'http://gdata.youtube.com/feeds/api/videos/J_DV9b0x7v4',
    'license': 'http://www.youtube.com/t/terms',
}
    
CARAMELL_DANSEN_SEARCH_DESCRIPTION = u"English: do-do-do-oo, yeah-yeah-yeah-yeah We wonder are you ready to join us now hands in the air we will show you how come and try caramell will be your guide So come and move your hips sing wha-aa look at hips, do it La-la-la you and me can sing this melody Oh-wa-aaa Dance to the beat Wave your hands together Come feel the heat forever and forever Listen and learn it is time for prancing Now we are here with caramel dancing Oo-oa-oa Oo-oa-oa-aa Oo-oa-oa Oo-oa-oa-aa From Sweden to UK we will bring our song, Australia, USA and people of Hong Kong. They have heard this meaning all around the world So come and move your hips sing wha-aa Look at your hips, do it La-la-la You and me can sing this melody So come and dance to the beat Wave your hands together Come feel the heat forever and forever Listen and learn it is time for prancing Now we are here with caramel dancing (Dance to the beat wave your hands together come feel the heat forever and forever listen and learn it is time for prancing now we are here with caramel dancing) Uu-ua-ua Uu-ua-ua-aa Uu-ua-ua Uu-ua-ua-aa So come and dance to the beat Wave your hands together Come feel the heat forever and forever Listen and learn it is time for prancing Now we are here with caramel dancing... Dance to the beat Wave your hands together Come feel the heat forever and forever Listen and learn it is time for prancing Now we are here with caramel dancing Swedish: Vi undrar \xe4r ni redo att vara med Armarna upp nu ska ni f\xe5 se Kom <b>...</b>"


class YouTubeTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.suite = YouTubeSuite()
        self.url = "http://www.youtube.com/watch?v=J_DV9b0x7v4"


class YouTubeSuiteTestCase(YouTubeTestCase):
    def test_available_fields(self):
        self.assertEqual(
            self.suite.available_fields,
            set(['embed_code', 'description', 'flash_enclosure_url', 'title',
                 'file_url_mimetype', 'user_url', 'file_url',
                 'thumbnail_url', 'link', 'user', 'guid',
                 'publish_datetime', 'tags', 'file_url_expires', 'license']))


class YouTubePathTestCase(YouTubeTestCase):
    def test_valid_urls(self):
        mixin = YouTubePathMixin()
        valid_urls = (
            ({'video_id': 'J_DV9b0x7v4'},
             ('http://youtu.be/J_DV9b0x7v4',
              'http://www.youtube.com/watch?feature=youtu.be&v=J_DV9b0x7v4',
              'http://www.youtube.com/watch?&v=J_DV9b0x7v4')),
            ({'video_id': "ZSh_c7-fZqQ"},
             ("http://www.youtube.com/watch?v=ZSh_c7-fZqQ",)),
        )
        invalid_urls = (
            'http://youtube.com/'
        )
        for expected, urls in valid_urls:
            for url in urls:
                self.assertEqual(mixin.get_url_data(url), expected)

        for url in invalid_urls:
            self.assertRaises(UnhandledURL, mixin.get_url_data, url)


class YouTubeOembedTestCase(YouTubeTestCase):
    def setUp(self):
        YouTubeTestCase.setUp(self)
        self.loader = YouTubeOEmbedLoader(self.url)

    def test_forbidden(self):
        expected_data = {'is_embeddable': False}
        response = self.get_response('', code=requests.codes.forbidden)
        data = self.loader.get_video_data(response)
        self.assertDictEqual(data, expected_data)

    def test_unauthorized(self):
        expected_data = {'is_embeddable': False}
        response = self.get_response('', code=requests.codes.unauthorized)
        data = self.loader.get_video_data(response)
        self.assertDictEqual(data, expected_data)

    def test_404(self):
        response = self.get_response('', code=404)
        data = self.loader.get_video_data(response)
        self.assertEqual(data, {})


class YouTubeApiTestCase(YouTubeTestCase):
    def setUp(self):
        YouTubeTestCase.setUp(self)
        self.loader = YouTubeApiLoader(self.url)

    def test_get_url(self):
        api_url = self.loader.get_url()
        self.assertEqual(
            api_url,
            "http://gdata.youtube.com/feeds/api/videos/J_DV9b0x7v4?v=2&alt=json")
        loader = YouTubeApiLoader("http://www.youtube.com/watch?v=ZSh_c7-fZqQ")
        api_url = loader.get_url()
        self.assertEqual(
            api_url,
            "http://gdata.youtube.com/feeds/api/videos/ZSh_c7-fZqQ?v=2&alt=json")

    def test_get_video_data(self):
        api_file = self.get_data_file('youtube/api.json')
        response = self.get_response(api_file.read())
        data = self.loader.get_video_data(response)
        self.assertEqual(set(data), self.loader.fields)
        data['tags'] = set(data['tags'])
        self.assertDictEqual(data, CARAMELL_DANSEN_API_DATA)

    def test_get_video_data__forbidden(self):
        expected_data = {'is_embeddable': False}
        response = self.get_response('', code=requests.codes.forbidden)
        data = self.loader.get_video_data(response)
        self.assertDictEqual(data, expected_data)

    def test_get_video_data__unauthorized(self):
        expected_data = {'is_embeddable': False}
        response = self.get_response('', code=requests.codes.unauthorized)
        data = self.loader.get_video_data(response)
        self.assertDictEqual(data, expected_data)

    def test_get_video_data__restricted(self):
        api_file = self.get_data_file('youtube/restricted_api.json')
        response = self.get_response(api_file.read())
        data = self.loader.get_video_data(response)
        self.assertTrue(isinstance(data, dict))
        self.assertEqual(data['description'],
                         "Like dolphins, whales communicate using sound. \
Humpbacks especially have extremely complex communication systems.")

    def test_get_video_data__missing_keywords(self):
        api_file = self.get_data_file('youtube/missing_keywords.json')
        response = self.get_response(api_file.read())
        data = self.loader.get_video_data(response)
        self.assertTrue(isinstance(data, dict))
        self.assertEqual(data['tags'], ['Nonprofit'])

class YouTubeScrapeTestCase(YouTubeTestCase):
    def setUp(self):
        YouTubeTestCase.setUp(self)
        self.loader = YouTubeScrapeLoader(self.url)

    def test_get_url(self):
        scrape_url = self.loader.get_url()
        self.assertEqual(
            scrape_url,
            ('http://www.youtube.com/get_video_info?video_id=J_DV9b0x7v4&'
             'el=embedded&ps=default&eurl='))

    def test_get_video_data(self):
        scrape_file = self.get_data_file('youtube/scrape.txt')
        response = self.get_response(scrape_file.read())
        data = self.loader.get_video_data(response)
        self.assertEqual(set(data), self.loader.fields)
        expected_data = {
            'title': u'CaramellDansen (Full Version + Lyrics)',
            'thumbnail_url': 'http://i3.ytimg.com/vi/J_DV9b0x7v4/hqdefault.jpg',
            'user': u'DrunkenVuko',
            'user_url': u'http://www.youtube.com/user/DrunkenVuko',
            'tags': [u'caramell', u'dance', u'dansen', u'hip', u'hop',
                     u's\xfcchtig', u'geil', u'cool', u'lustig', u'manga',
                     u'schweden', u'anime', u'musik', u'music', u'funny',
                     u'caramelldansen', u'U-U-U-Aua', u'Dance'],
            'file_url_expires': datetime.datetime(2011, 11, 30, 1, 0),
            'file_url_mimetype': u'video/x-flv',
            'file_url': 'http://o-o.preferred.comcast-lga1.v6.lscache7.c.youtube.com/videoplayback?sparams=id%2Cexpire%2Cip%2Cipbits%2Citag%2Csource%2Calgorithm%2Cburst%2Cfactor%2Ccp&fexp=914999%2C908425&algorithm=throttle-factor&itag=5&ip=71.0.0.0&burst=40&sver=3&signature=67657D04EC6665D74BD0B736A9C3C3305B41A72B.48096D7D9D9D1DB4BEDF185A14B15AA19DE2A9C6&source=youtube&expire=1322614800&key=yt1&ipbits=8&factor=1.25&cp=U0hRR1ZMUl9FSkNOMV9ORlZJOmNUdWlkbTNrcU4y&id=27f0d5f5bd31eefe&quality=small&fallback_host=tc.v6.cache7.c.youtube.com&type=video/x-flv&itag=5',
        }
        self.assertDictEqual(data, expected_data)

    def test_get_video_data__fail_150(self):
        scrape_file = self.get_data_file('youtube/scrape2.txt')
        response = self.get_response(scrape_file.read())
        data = self.loader.get_video_data(response)
        self.assertDictEqual(data, {'is_embeddable': False})

    def test_get_video_data__fail_other(self):
        scrape_file = self.get_data_file('youtube/scrape2.txt')
        scrape_data = scrape_file.read().replace('150', 'other')
        response = self.get_response(scrape_data)
        data = self.loader.get_video_data(response)
        self.assertEqual(data, {})

    def test_get_video_data__402(self):
        response = self.get_response('', code=402)
        data = self.loader.get_video_data(response)
        self.assertEqual(data, {})


class YouTubeFeedTestCase(YouTubeTestCase):
    def setUp(self):
        YouTubeTestCase.setUp(self)
        self.feed_url = ('http://gdata.youtube.com/feeds/api/users/'
                         'AssociatedPress/uploads?alt=json&v=2&start-index=1'
                         '&max-results=5')
        self.feed = self.suite.get_feed(self.feed_url)
        feed_file = self.get_data_file('youtube/feed.json')
        self.response = self.get_response(feed_file.read())
        self.response._parsed = json.loads(self.response.text)

    def test_feed_urls(self):
        valid_urls = (
            'youtube.com/associatedpress',
            'www.youtube.com/associatedpress',
            'www.youtube.com/user/associatedpress',
            'www.youtube.com/profile/?user=associatedpress',
            'www.youtube.com/profile_videos/?user=associatedpress',
            'gdata.youtube.com/feeds/base/users/associatedpress',
            'gdata.youtube.com/feeds/api/users/associatedpress',
        )
        invalid_urls = (
            'http://www.youtube.com/profile/',
        )
        for scheme in ('http', 'https'):
            for url in valid_urls:
                data = self.feed.get_url_data("{0}://{1}".format(scheme, url))
                self.assertEqual(data['username'], 'associatedpress')

        for url in invalid_urls:
            self.assertRaises(UnhandledURL, self.feed.get_url_data, url)

    def test_data_from_response(self):
        expected = {
            'video_count': 56618,
            'title': u'Uploads by AssociatedPress',
            'webpage': u'http://www.youtube.com/user/AssociatedPress/videos',
            'guid': u'tag:youtube.com,2008:user:AssociatedPress:uploads',
            'etag': u'W/"C0AEQX0_eip7I2A9WhVQFUs."',
            'thumbnail_url': 'http://www.youtube.com/img/pic_youtubelogo_123x63.gif',
        }
        data = self.feed.data_from_response(self.response)
        self.assertEqual(data, expected)

    def test_get_page_url(self):
        url = self.feed.get_page_url(page_start=3, page_max=25)
        self.assertEqual(url, 'http://gdata.youtube.com/feeds/api/users/'
                              'AssociatedPress/uploads?alt=json&v=2&'
                              'start-index=3&max-results=25')

    def test_get_video_data(self):
        expected = {
            'description': u'GOP presidential candidate Mitt Romney said '
                            'President Barack Obama is being coy about his '
                            'long-term plans for a missile defense system in '
                            'Europe and other issues. He said now is not the '
                            'time for a "hide and seek" strategy by a '
                            'president. (April 4)',
            'guid': 'http://gdata.youtube.com/feeds/api/videos/RLISBF9-G30',
            'link': u'http://www.youtube.com/watch?v=RLISBF9-G30',
             'publish_datetime': datetime.datetime(2012, 4, 4, 17, 41, 49),
             'tags': [u'romney', u'News'],
             'thumbnail_url':
                 u'http://i.ytimg.com/vi/RLISBF9-G30/hqdefault.jpg',
             'title': u'Romney Says Obama Not Being Candid',
             'user': u'AssociatedPress',
             'user_url': u'http://www.youtube.com/user/AssociatedPress',
             'flash_enclosure_url': u'http://www.youtube.com/watch?v=RLISBF9-G30&feature=youtube_gdata_player',
             'license': u'http://www.youtube.com/t/terms',
        }
        entries = self.feed.get_response_items(self.response)
        data = self.feed.get_video_data(entries[0])
        self.assertEqual(data, expected)

class YouTubeSearchTestCase(YouTubeTestCase):
    def setUp(self):
        YouTubeTestCase.setUp(self)
        search_file = self.get_data_file('youtube/search.json')
        response = self.get_response(search_file.read())
        response._parsed = json.loads(response.text)
        self.search = self.suite.get_search('query')
        self.results = self.search.get_response_items(response)

    def test_parse_search_result(self):
        data = self.search.get_video_data(self.results[0])
        self.assertTrue(isinstance(data, dict))
        data['tags'] = set(data['tags'])
        expected_data = CARAMELL_DANSEN_API_DATA.copy()
        expected_data['description'] = CARAMELL_DANSEN_SEARCH_DESCRIPTION
        # TODO: Perhaps google will fix this strange difference someday.
        if 'UUU-Aua' in data['tags']:
            data['tags'].remove('UUU-Aua')
            data['tags'].add('U-U-U-Aua')
        self.assertEqual(data, expected_data)

    def test_get_page_url_data(self):
        data = self.search.get_page_url_data(1, 5)
        for key in ('query', 'order_by', 'page_start', 'page_max'):
            self.assertTrue(key in data, "key {0} not found".format(key))
