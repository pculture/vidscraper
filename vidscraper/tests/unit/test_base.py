from vidscraper.exceptions import UnhandledVideo
from vidscraper.suites.base import BaseSuite
from vidscraper.tests.base import BaseTestCase


class BaseSuiteTestCase(BaseTestCase):
    def test_get_video__no_url(self):
        suite = BaseSuite()
        self.assertRaises(UnhandledVideo, suite.get_video, None)
        self.assertRaises(UnhandledVideo, suite.get_video, '')
