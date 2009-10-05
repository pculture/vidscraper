import urllib2
import re

import feedparser

from vidscraper.bulk_import import util

VIDEO_COUNT_RE = re.compile('totalPages: (\d+)')

_cached_video_count = {}

def video_count(parsed_feed):
    if 'generator_detail' not in parsed_feed or \
            parsed_feed.feed.generator_detail.get('name') != 'http://blip.tv':
        # not a blip.tv feed
        return None
    if parsed_feed.feed.link in _cached_video_count:
        return _cached_video_count[parsed_feed.feed.link]
    base_url = parsed_feed.feed.summary_detail.base
    json_data = urllib2.urlopen(base_url.replace(
            '/rss', '/posts?skin=json&version=3&page=1000')).read()
    # it's approximate, but we can't get the real count without loading an
    # extra page
    # We cache the count to avoid the extra API call in the default case (
    # bulk_import.video_count() followed by bulk_import.bulk_import() (which
    # calls us again).
    _cached_video_count[parsed_feed.feed.link] = count = \
        int(VIDEO_COUNT_RE.search(json_data).group(1)) * 12

    return count


def bulk_import(parsed_feed):
    base_url = parsed_feed.feed.summary_detail.base
    feeds = []
    while len(parsed_feed.entries):
        feeds.append(parsed_feed)
        parsed_feed = feedparser.parse(
            '%s?page=%i' % (base_url,
                            len(feeds) + 1))

    # clear the count cache
    if parsed_feed.feed.link in _cached_video_count:
        del _cached_video_count[parsed_feed.feed.link]

    return util.join_feeds(feeds)
