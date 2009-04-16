import urllib

import feedparser

#'http://gdata.youtube.com/feeds/api/videos?vq=%s&amp;alt=rss'
YOUTUBE_QUERY_BASE = 'http://gdata.youtube.com/feeds/api/videos'

def parse_feedparser_entry(entry):
    return {
        'title': entry['title'],
        'description': entry['summary'],
        'link': entry['link'],
     }


def get_entries(include_terms, exclude_terms=None, orderby='relevant'):
    search_terms = '+'.join(include_terms)
    if exclude_terms:
        search_terms += '+' + '+'.join(['-' + term for term in exclude_terms])

    get_params = {
        'vq': search_terms,
        'alt': 'rss'}

    if orderby == 'latest':
        get_params['orderby'] = 'published'
    elif orderby == 'relevant':
        get_params['orderby'] = 'relevance'
    else:
        pass #TODO: throw an error here

    get_url = '%s?%s' % (YOUTUBE_QUERY_BASE, urllib.urlencode(get_params))

    parsed_feed = feedparser.parse(get_url)

    return [parse_feedparser_entry(entry) for entry in parsed_feed.entries]


SUITE = {
    'id': 'youtube',
    'display_name': 'YouTube',
    'orderbys': ['latest', 'relevant'],
    'func': get_entries}
