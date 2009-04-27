import cgi
import re
import simplejson
import urllib
import urlparse

import feedparser
from lxml import builder
from lxml import etree
from lxml.html import builder as E
from lxml.html import tostring
from lxml.html.clean import clean_html

from vidscraper.decorators import provide_shortmem, parse_url, returns_unicode
from vidscraper import errors, util


EMaker = builder.ElementMaker()
EMBED = EMaker.embed

EMBED_WIDTH = 425
EMBED_HEIGHT = 344


def parse_feed(scraper_func):
    def new_scraper_func(url, shortmem=None, *args, **kwargs):
        if not shortmem.get('feed_item'):
            file_id = BLIP_REGEX.match(url).groupdict()['file_id']
            rss_url = 'http://blip.tv/file/%s?skin=rss' % file_id
            shortmem['feed_item'] = feedparser.parse(rss_url)['entries'][0]

        return scraper_func(url, shortmem=shortmem, *args, **kwargs)

    return new_scraper_func



@provide_shortmem
@parse_feed
@returns_unicode
def scrape_title(url, shortmem=None):
    try:
        return shortmem['feed_item']['title']
    except KeyError:
        raise errors.FieldNotFound('Could not find the title field')


@provide_shortmem
@parse_feed
@returns_unicode
def scrape_description(url, shortmem=None):
    try:
        return util.clean_description_html(
            shortmem['feed_item']['summary_detail']['value'])
    except KeyError:
        raise errors.FieldNotFound('Could not find the title field')


@provide_shortmem
def get_embed(url, shortmem=None, width=EMBED_WIDTH, height=EMBED_HEIGHT):
    file_id = BLIP_REGEX.match(url).groupdict()['file_id']
    oembed_get_dict = {
            'url': 'http://blip.tv/file/%s' % file_id,
            'width': EMBED_WIDTH,
            'height': EMBED_HEIGHT}
    
    oembed_response = urllib.urlopen(
        'http://blip.tv/oembed/?' + urllib.urlencode(oembed_get_dict)).read()


    try:
        embed_code = simplejson.loads(oembed_response.decode('utf8'))['html']
    except ValueError:
        embed_code = None

    return embed_code


BLIP_REGEX = re.compile(r'^http://blip.tv/file/(?P<file_id>\d+)')
SUITE = {
    'regex': BLIP_REGEX,
    'funcs': {
        'title': scrape_title,
        'description': scrape_description,
        'embed': get_embed}}
