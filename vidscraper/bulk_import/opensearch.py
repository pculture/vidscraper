import urlparse
import urllib

import feedparser

from vidscraper.bulk_import import util

# add the OpenSearch namespace to FeedParser
# http://code.google.com/p/feedparser/issues/detail?id=55
feedparser._FeedParserMixin.namespaces[
    'http://a9.com/-/spec/opensearch/1.1/'] = 'opensearch'


def _opensearch_get(parsed_feed, key):
    return (parsed_feed.feed.get('opensearch_%s' % key) or
            parsed_feed.feed.get(key, None))

def video_count(parsed_feed):
    """
    Returns the number of videos that we think are in this feed in total.  If
    the feed isn't a valid OpenSearch feed, return None.
    """
    if not (_opensearch_get(parsed_feed, 'startindex') and
            _opensearch_get(parsed_feed, 'itemsperpage') and
            _opensearch_get(parsed_feed, 'totalresults')):
        return None # not a valid OpenSearch feed
    return int(_opensearch_get(parsed_feed, 'totalresults'))

def bulk_import_url_list(parsed_feed):
    feed_url = getattr(parsed_feed, 'href', None)
    if feed_url is None:
        # Google-specific hack:
        back_to_us = [link for link in parsed_feed.feed.links
                      if link['rel'] == 'self']
        feed_url = back_to_us[0]['href']

    startindex = int(_opensearch_get(parsed_feed, 'startindex'))
    itemsperpage = int(_opensearch_get(parsed_feed, 'itemsperpage'))
    totalresults = int(_opensearch_get(parsed_feed, 'totalresults'))
    feeds = []
    feed_url_parsed = urlparse.urlparse(feed_url)

    for i in range(startindex, max(totalresults, itemsperpage),
                   itemsperpage):

        query_dict = dict(urlparse.parse_qsl(feed_url_parsed.query))
        query_dict['start-index'] = str(i)
        new_query_string = urllib.urlencode(query_dict)
        new_urlparse_data = (feed_url_parsed.scheme,
                             feed_url_parsed.netloc,
                             feed_url_parsed.path,
                             feed_url_parsed.params,
                             new_query_string,
                             feed_url_parsed.fragment)

        feed_url = urlparse.urlunparse(new_urlparse_data)
        feeds.append(feed_url)

    return feeds

def bulk_import(parsed_feed):
    url_list = bulk_import_url_list(parsed_feed)
    feeds = [feedparser.parse(url) for url in url_list]
    return util.join_feeds(feeds)

