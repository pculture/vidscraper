import feedparser

from vidscraper.bulk_import import opensearch, blip, vimeo
from vidscraper import miroguide_util

IMPORTERS = (
    opensearch,
    blip,
    vimeo,
    )

def bulk_import_url_list(parsed_feed):
    """
    Takes a parsed feed, and either:

    * Returns a list of URLs that you can pass to feedparser, or
    * Raises ValueError.

    If you get ValueError, you should call bulk_import instead because the
    IMPORTER that we chose does not support bulk_import_url_list.
    """
    for importer in IMPORTERS:
        if importer.video_count(parsed_feed) is not None:
            # Then this importer thinks it can provide data about the feed.
            fn = getattr(importer, 'bulk_import_url_list', None)
            if fn is not None:
                return fn(parsed_feed)

    raise ValueError, ("We cannot geneate a list of feed URLs for " +
                       "the feed you gave us.")

def bulk_import(feed_url, parsed_feed=None):
    """
    Takes a URL for a feed, and returns a feedparser instance with the entries
    filled in with all of the videos from that feed.  It'll take care of paging
    through videos from services like blip.tv and Vimeo or services which
    support OpenSearch (like YouTube).
    """
    if parsed_feed is None:
        parsed_feed = feedparser.parse(feed_url)
    for importer in IMPORTERS:
        if importer.video_count(parsed_feed) is not None:
            return importer.bulk_import(parsed_feed)

    # if we can't figure out how to bulk import the feed, just return the items
    # in the feed
    return parsed_feed


def video_count(feed_url, parsed_feed=None):
    """
    Takes a URL for a feed, and returns the number of videos we think we can
    import from it.
    """
    if parsed_feed is None:
        parsed_feed = feedparser.parse(feed_url)
    for importer in IMPORTERS:
        count = importer.video_count(parsed_feed)
        if count is not None:
            return count

    count = 0
    for entry in parsed_feed.entries:
        if miroguide_util.get_first_video_enclosure(entry) is not None:
            count += 1
    return count
