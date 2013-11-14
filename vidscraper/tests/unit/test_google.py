from vidscraper.suites.google import Suite, ScrapeLoader
from vidscraper.tests.base import BaseTestCase


class GoogleTestCase(BaseTestCase):
    def setUp(self):
        self.suite = Suite()


class GoogleScrapeTestCase(GoogleTestCase):
    def setUp(self):
        GoogleTestCase.setUp(self)
        self.url = "http://video.google.com/videoplay?docid=3372610739323185039"
        self.loader = ScrapeLoader(self.url)

    def test_get_url(self):
        self.assertEqual(self.loader.get_url(), self.url)

    def test_get_video_data(self):
        scrape_file = self.get_data_file('google/scrape.html')
        response = self.get_response(scrape_file.read())
        data = self.loader.get_video_data(response)
        self.assertTrue(isinstance(data, dict))
        self.assertEqual(set(data), self.loader.fields)
        expected_data = {
            'title': "Tom and Jerry. Texas",
            'description': 'Tom and Jerry.',
            'embed_code': """<embed id="VideoPlayback" \
src="http://video.google.com/googleplayer.swf?docid=3372610739323185039&\
hl=en&fs=true" style="width:400px;height:326px" allowFullScreen="true" \
allowScriptAccess="always" type="application/x-shockwave-flash"> </embed>"""
        }
        self.assertDictEqual(data, expected_data)
