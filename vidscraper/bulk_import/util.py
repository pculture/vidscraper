def join_feeds(feeds):
    """
    Takes an interable of feedparser instances, and returns a single feedparser
    intance with the entries from each combined into one.
    """
    entries = []
    [entries.extend(feed.entries) for feed in feeds]
    feed = feeds[0]
    feed.entries = entries
    return feed
