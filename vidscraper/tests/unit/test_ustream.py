import datetime

from vidscraper.exceptions import UnhandledVideo
from vidscraper.suites.ustream import (Suite, ApiLoader,
                                       OEmbedLoader)
from vidscraper.tests.base import BaseTestCase


class UstreamTestCase(BaseTestCase):
    def setUp(self):
        self.suite = Suite()


class UstreamApiTestCase(UstreamTestCase):
    def setUp(self):
        UstreamTestCase.setUp(self)
        self.url = "http://www.ustream.tv/recorded/16417223"
        self.loader = ApiLoader(self.url,
                                       api_keys={'ustream_key': 'TEST_KEY'})

    def test_keys_required(self):
        self.assertRaises(UnhandledVideo, ApiLoader, self.url)

    def test_get_url(self):
        api_url = self.loader.get_url()
        self.assertEqual(api_url,
            'http://api.ustream.tv/json/video/16417223/getInfo/?key=TEST_KEY')

    def test_get_video_data(self):
        expected_data = {
            'link': u'http://www.ustream.tv/recorded/16417223',
            'description': u'President Obama Speaks Live From His Birthday Event',
            'flash_enclosure_url': u'http://www.ustream.tv/flash/video/16417223',
            'title': u'President Obama Speaks Live From His Birthday Event',
            'publish_date': datetime.datetime(2011, 8, 3, 17, 16, 55),
            'tags': [u'Barack', u'Live', u'Obama', u'Ustream', u'on'],
            'thumbnail_url': u'http://static-cdn2.ustream.tv/videopic/0/1/16/16417/16417223/1_203240_16417223_320x240_b_1:2.jpg',
            'user_url': u'http://www.ustream.tv/user/ObamaForAmerica',
            'user': u'ObamaForAmerica'
        }
        api_file = self.get_data_file('ustream/api.json')
        response = self.get_response(api_file.read())
        data = self.loader.get_video_data(response)
        self.assertEqual(set(data), self.loader.fields)
        self.assertDictEqual(data, expected_data)


class UstreamOEmbedTestCase(UstreamTestCase):
    def test_valid_urls(self):
        url = "http://www.ustream.tv/recorded/16417223"
        result = OEmbedLoader(url).get_url()
        expected = "http://www.ustream.tv/oembed/?url=http%3A%2F%2Fwww.ustream.tv%2Frecorded%2F16417223"
        self.assertEqual(result, expected)
