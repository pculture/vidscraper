import urlparse

import feedparser

from vidscraper.exceptions import UnhandledFeed
from vidscraper.suites import BaseSuite, registry
from vidscraper.utils.feedparser import (get_accepted_enclosures,
                                         struct_time_to_datetime)
from vidscraper.videos import FeedparserFeed, VideoFile


# add the Kaltura namespace to FeedParser.
# http://code.google.com/p/feedparser/issues/detail?id=55
feedparser._FeedParserMixin.namespaces[
    'http://kaltura.com/playlist/1.0'] = 'kaltura'


class Feed(FeedparserFeed):
    schemes = ('http', 'https')
    netlocs = ('kaltura.com', 'www.kaltura.com')
    path = '/index.php/partnerservices2/executeplaylist'
    page_url_format = ('http://www.kaltura.com/index.php/partnerservices2/'
                       'executeplaylist?format=8&partner_id={partner_id}'
                       '&subp_id={subp_id}&playlist_id={playlist_id}')

    def _next_page(self):
        if self.start_index != 1 or self.item_count > 0:
            raise StopIteration
        super(Feed, self)._next_page()

    def get_url_data(self, url):
        parsed_url = urlparse.urlsplit(url)
        if (parsed_url.scheme in self.schemes and
                parsed_url.netloc in self.netlocs and
                parsed_url.path == self.path):
            parsed_qs = urlparse.parse_qs(parsed_url.query)
            try:
                return {
                    'partner_id': parsed_qs['partner_id'][0],
                    'subp_id': parsed_qs['subp_id'][0],
                    'playlist_id': parsed_qs['playlist_id'][0],
                }
            except (KeyError, IndexError):
                pass

        raise UnhandledFeed(url)

    def get_video_data(self, item):
        files = [VideoFile(url=enclosure.get('url'),
                           mime_type=enclosure.get('type'),
                           length=(enclosure.get('filesize') or
                                   enclosure.get('length')))
                 for enclosure in get_accepted_enclosures(item)]

        data = {
            'title': item.title,
            'description': item.description,
            'thumbnail_url': item.media_thumbnail[0]['url'],
            'publish_datetime': struct_time_to_datetime(item.published_parsed),
            'user': item['kaltura_userscreenname'],
            'files': files or None,
        }
        return data


class Suite(BaseSuite):
    feed_class = Feed


registry.register(Suite)
