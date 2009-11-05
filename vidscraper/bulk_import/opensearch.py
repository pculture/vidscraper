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

def bulk_import(parsed_feed):
    startindex = int(_opensearch_get(parsed_feed, 'startindex'))
    itemsperpage = int(_opensearch_get(parsed_feed, 'itemsperpage'))
    totalresults = int(_opensearch_get(parsed_feed, 'totalresults'))
    feeds = []
    for i in range(startindex, max(totalresults, itemsperpage),
                   itemsperpage):
        if '?' in parsed_feed.href:
            postfix = '&start-index=%i' % (i,)
        else:
            postfix = '?start-index=%i' % (i,)
        feeds.append(feedparser.parse(parsed_feed.href + postfix))

    return util.join_feeds(feeds)

