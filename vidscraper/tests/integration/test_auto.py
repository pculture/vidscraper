import datetime

from vidscraper import auto_scrape, auto_search, auto_feed
from vidscraper.tests.base import BaseTestCase


class AutoIntegrationTestCase(BaseTestCase):
    def test_auto_scrape(self):
        video = auto_scrape("http://www.youtube.com/watch?v=J_DV9b0x7v4")
        self.assertEqual(video.title,
                         u'CaramellDansen (Full Version + Lyrics)')
        self.assertGreater(len(video.files), 0)
        self.assertTrue(video.files[0].url)
        self.assertEqual(video.files[0].mime_type, u'video/mp4')
        self.assertTrue(
            video.files[0].expires - datetime.datetime.now() >
            datetime.timedelta(hours=1))

    def test_auto_search(self):
        searches = auto_search('parrot -dead', max_results=20)
        results = []
        for search in searches:
            videos = list(search)
            self.assertTrue(len(videos) <= 20,
                            "{0} search has too many results ({1})".format(
                                search.__class__.__name__, len(videos)))
            results.extend(videos)
        self.assertTrue(len(videos) > 0)

    def test_auto_feed(self):
        max_results = 20
        feed = auto_feed("http://youtube.com/AssociatedPress",
                         max_results=max_results)
        self.assertEqual(feed.url,
                         "http://youtube.com/AssociatedPress")
        self.assertEqual(feed.url_data, {'username': 'AssociatedPress'})
        feed.load()
        self.assertEqual(feed.title, 'Uploads by AssociatedPress')
        self.assertEqual(
            feed.thumbnail_url,
            'http://www.youtube.com/img/pic_youtubelogo_123x63.gif')
        # YouTube changes this sometimes, so just make sure it's there
        self.assertTrue(feed.webpage)
        self.assertTrue(feed.etag is not None)
        self.assertTrue(feed.video_count > 55000)
        self.assertEqual(feed.guid,
                         u'tag:youtube.com,2008:user:AssociatedPress:uploads')
        videos = list(feed)
        self.assertEqual(len(videos), max_results)
