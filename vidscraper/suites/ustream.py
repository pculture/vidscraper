import datetime
import json
import re
import urlparse

from vidscraper.exceptions import UnhandledVideo
from vidscraper.suites import BaseSuite, registry
from vidscraper.videos import VideoLoader, OEmbedLoaderMixin


class PathMixin(object):
    path_re = re.compile(r'/recorded/(?P<id>\d+)/?$')

    def get_url_data(self, url):
        parsed_url = urlparse.urlsplit(url)
        if (parsed_url.scheme in ('http', 'https') and
            parsed_url.netloc in ('ustream.tv', 'www.ustream.tv')):
            match = self.path_re.match(parsed_url.path)
            if match:
                return match.groupdict()
        raise UnhandledVideo(url)


class ApiLoader(PathMixin, VideoLoader):
    fields = set(['link', 'title', 'description', 'flash_enclosure_url',
                  'thumbnail_url', 'publish_date', 'tags', 'user',
                  'user_url'])

    url_format = u'http://api.ustream.tv/json/video/{id}/getInfo/?key={ustream_key}'

    def get_url_data(self, url):
        if 'ustream_key' not in self.api_keys:
            raise UnhandledVideo(url)
        data = super(ApiLoader, self).get_url_data(url)
        data.update(self.api_keys)
        return data

    def get_video_data(self, response):
        parsed = json.loads(response.text)['results']
        url = parsed['embedTagSourceUrl']
        publish_date = datetime.datetime.strptime(parsed['createdAt'],
                                                 '%Y-%m-%d %H:%M:%S')
        data = {
            'link': parsed['url'],
            'title': parsed['title'],
            'description': parsed['description'],
            'flash_enclosure_url': url,
            'thumbnail_url': parsed['imageUrl']['medium'],
            'publish_date': publish_date,
            'tags': [unicode(tag) for tag in parsed['tags']],
            'user': parsed['user']['userName'],
            'user_url': parsed['user']['url']
        }
        return data


class OEmbedLoader(OEmbedLoaderMixin, PathMixin, VideoLoader):
    endpoint = "http://www.ustream.tv/oembed/"
    url_format = "http://www.ustream.tv/recorded/{id}"


class Suite(BaseSuite):
    """Suite for fetching data on ustream videos."""
    # TODO: Ustream has feeds and search functionality - add support for that!
    loader_classes = (OEmbedLoader, ApiLoader)


registry.register(Suite)
