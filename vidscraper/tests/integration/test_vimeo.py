import datetime

from vidscraper.suites.vimeo import Suite
from vidscraper.tests.base import BaseTestCase


class VimeoIntegrationTestCase(BaseTestCase):

    def setUp(self):
        self.suite = Suite()

    def test_video(self):
        video_url = u'http://vimeo.com/7981161'
        video = self.suite.get_video(video_url)
        video.load()
        expected = {
            'description':
                'Tishana from SPARK Reproductive Justice talking about the \
right to choose after the National Day of Action Rally to Stop Stupak-Pitts, \
12.2.2009',
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
            print value, getattr(video, key)
            self.assertEqual(value, getattr(video, key))

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
        data = dict((key, getattr(feed, key)) for key in expected)
        self.assertEqual(data, expected)

        self.assertTrue(feed.video_count > 30, feed.video_count)
