import re
import urlparse

from bs4 import BeautifulSoup

from vidscraper.exceptions import UnhandledVideo
from vidscraper.suites import BaseSuite, registry
from vidscraper.videos import VideoLoader


class ScrapeLoader(VideoLoader):
    fields = set(['title', 'description', 'embed_code'])
    id_regex = re.compile(r'video-title|video-description|embed-video-code')

    url_format = '{url}'

    def get_url_data(self, url):
        parsed = urlparse.urlsplit(url)
        if (parsed.scheme in ('http', 'https') and
            parsed.netloc == 'video.google.com' and
            parsed.path == '/videoplay' and
            'docid' in parsed.query):
            return {'url': url}
        raise UnhandledVideo(url)

    def get_video_data(self, response):
        soup = BeautifulSoup(response.text).findAll(id=self.id_regex)
        data = {}
        for tag in soup:
            if tag['id'] == 'video-title':
                data['title'] = unicode(tag.string)
            elif tag['id'] == 'video-description':
                data['description'] = ''.join((unicode(t) for t in tag)).strip()
            elif tag['id'] == 'embed-video-code':
                # This isn't the cleanest way of handling the gt/lt problem,
                # but this is a scrape and liable to break anyway. KISS.
                data['embed_code'] = unicode(tag.string).replace("&gt;", ">").replace("&lt;", "<")
        return data


class Suite(BaseSuite):
    """Suite for scraping video pages from videos.google.com"""
    loader_classes = (ScrapeLoader,)


registry.register(Suite)
