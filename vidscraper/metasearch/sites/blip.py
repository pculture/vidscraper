import urllib

import feedparser

from vidscraper.metasearch import util as metasearch_util
from vidscraper.sites import blip as blip_scraper

#'http://www.blip.tv/search/?search=(string)skin=rss'
BLIP_QUERY_BASE = 'http://blip.tv/search/'


def parse_entry(entry):
    parsed_entry = {
        'title': entry['title'],
        'description':
            entry.get('summary') or entry.get('blip_puredescription') or \
            entry.get('puredescription') or '',
        'link': entry['link'],
        'thumbnail_url': entry.get('blip_picture'),
        'tags': [tag['term'] for tag in entry.tags]
        }
    parsed_entry['embed'] = blip_scraper.get_embed(entry['link'])
    parsed_entry['publish_date'] = blip_scraper.scrape_publish_date(
        entry['link'])

    return parsed_entry


def get_entries(include_terms, exclude_terms=None,
                order_by='relevant', **kwargs):
    search_string = metasearch_util.search_string_from_terms(
        include_terms, exclude_terms)

    get_params = {
        'skin': 'rss',
        'search': search_string}

    get_url = '%s?%s' % (BLIP_QUERY_BASE, urllib.urlencode(get_params))

    parsed_feed = feedparser.parse(get_url)

    return [parse_entry(entry) for entry in parsed_feed.entries]


SUITE = {
    'id': 'blip',
    'display_name': 'Blip.Tv',
    'order_bys': ['relevant'],
    'func': get_entries}
