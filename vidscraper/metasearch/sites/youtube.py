import urllib

import feedparser

from vidscraper.sites import youtube as youtube_scraper

#'http://gdata.youtube.com/feeds/api/videos?vq=%s&amp;alt=rss'
YOUTUBE_QUERY_BASE = 'http://gdata.youtube.com/feeds/api/videos'


def parse_youtube_entry(entry):
    parsed_entry = {
        'title': entry['title'],
        'description': entry['summary'],
        'link': entry['link']}
    parsed_entry['embed'] = youtube_scraper.get_embed(entry['link'])
    return parsed_entry


def get_entries(include_terms, exclude_terms=None,
                order_by='relevant', **kwargs):

    marked_exclude_terms = ['-' + term for term in exclude_terms or []]
    search_term_list = list(include_terms) + marked_exclude_terms
    search_terms = ' '.join(search_term_list)

    get_params = {
        'vq': search_terms,
        'alt': 'rss'}

    if order_by == 'latest':
        get_params['orderby'] = 'published'
    elif order_by == 'relevant':
        get_params['orderby'] = 'relevance'
    else:
        pass #TODO: throw an error here

    get_url = '%s?%s' % (YOUTUBE_QUERY_BASE, urllib.urlencode(get_params))

    parsed_feed = feedparser.parse(get_url)

    return [parse_youtube_entry(entry) for entry in parsed_feed.entries]


SUITE = {
    'id': 'youtube',
    'display_name': 'YouTube',
    'order_bys': ['latest', 'relevant'],
    'func': get_entries}
