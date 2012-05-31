import datetime
import pickle
import unittest

from vidscraper.suites import Video

class MockException(object):
    """
    This exception isn't pickleable because it defines __slots__ but not
    __getstate__. It lets us easily test behavior with unpickleable
    exceptions.

    """
    __slots__ = ('a', 'b', 'c')

class VideoTestCase(unittest.TestCase):

    def setUp(self):
        self.video = Video('http://www.youtube.com/watch?v=J_DV9b0x7v4')
        self.video.__dict__.update({
    'link': u'http://www.youtube.com/watch?v=J_DV9b0x7v4',
    'title': u'CaramellDansen (Full Version + Lyrics)',
    'description': u"Here's some description",
    'thumbnail_url': u'http://i.ytimg.com/vi/J_DV9b0x7v4/0.jpg',
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
        u"Music",
    ]),
    'publish_datetime': datetime.datetime(2007, 5, 7, 22, 15, 21),
    'guid': u'http://gdata.youtube.com/feeds/api/videos/J_DV9b0x7v4',})

    def test_pickle(self):
        """
        A filled out :class:`Video` instance is pickleable, and unpickling
        should result in another video.
        """
        data = pickle.dumps(self.video)
        video2 = pickle.loads(data)
        self.assertEqual(self.video.link, video2.link)

    def test_pickle_with_exception(self):
        """
        If the :class:`Video` instance has errors, they should be pickled along
        with the Video.
        """
        self.video._errors['scrape'] = TypeError()
        data = pickle.dumps(self.video)
        video2 = pickle.loads(data)
        self.assertEqual(self.video.link, video2.link)
        self.assertEqual(list(video2._errors.keys()), ['scrape'])
        self.assertTrue(isinstance(video2._errors['scrape'], TypeError))

    def test_pickle_with_unpickleable_exception(self):
        """
        If the :class:`Video` instance has errors, it is still pickleable even
        if the exception isn't. (A common example of an unpickleable
        exception would be a `urllib2.HTTPError`.)
        """
        self.video._errors['scrape'] = MockException()
        data = pickle.dumps(self.video)
        video2 = pickle.loads(data)
        self.assertEqual(self.video.link, video2.link)
        self.assertEqual(list(video2._errors.keys()), ['scrape'])

