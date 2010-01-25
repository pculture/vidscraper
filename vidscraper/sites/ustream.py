import datetime
import re
import urllib2

import simplejson

from vidscraper.decorators import provide_shortmem, returns_unicode
from vidscraper.errors import BaseUrlLoadFailure

USTREAM_API_KEY = None

def provide_api(func):
    """
    A quick decorator to provide the uStream API data for a video.
    """
    def wrapper(url, shortmem=None):
        if shortmem.get('results') is None:
            match = USTREAM_REGEX.match(url)
            id = match.group('id')
            api_file = urllib2.urlopen(
                'http://api.ustream.tv/json/video/%s/getInfo/?key=%s' % (
                    id, USTREAM_API_KEY))
            shortmem['results'] = simplejson.load(api_file)['results']
            if shortmem['results'] is None:
                raise BaseUrlLoadFailure('No results from uStream API')
        return func(url, shortmem)
    return wrapper

@provide_shortmem
@provide_api
@returns_unicode
def get_link(url, shortmem=None):
    return shortmem['results']['url']


@provide_shortmem
@provide_api
@returns_unicode
def get_title(url, shortmem=None):
    return shortmem['results'].get('title', '')


@provide_shortmem
@provide_api
@returns_unicode
def get_description(url, shortmem=None):
    return shortmem['results'].get('description')


@provide_shortmem
@provide_api
@returns_unicode
def get_flash_enclosure_url(url, shortmem=None):
    return shortmem['results']['embedTagSourceUrl']


@provide_shortmem
@provide_api
@returns_unicode
def get_embed(url, shortmem=None):
    tag = shortmem['results']['embedTag']
    start = tag.find('<embed ')
    end = tag.find(' />', start)
    tag = tag[start:end + 3]
    for attr in 'id', 'name':
        start = tag.find('%s="' % attr)
        end = tag.find('"', start + len(attr) + 2)
        tag = tag[:start] + tag[end+2:]
    return tag


@provide_shortmem
@provide_api
@returns_unicode
def get_thumbnail_url(url, shortmem=None):
    return shortmem['results']['imageUrl']['medium']



@provide_shortmem
@provide_api
def get_publish_date(url, shortmem=None):
    return datetime.datetime.strptime(shortmem['results']['createdAt'],
                                      '%Y-%m-%d %H:%M:%S')


@provide_shortmem
@provide_api
def get_tags(url, shortmem=None):
    return [tag.decode('utf8') for tag in shortmem['results']['tags']]


@provide_shortmem
@provide_api
@returns_unicode
def get_user(url, shortmem=None):
    return shortmem['results']['user']['userName']


@provide_shortmem
@provide_api
@returns_unicode
def get_user_url(url, shortmem=None):
    return shortmem['results']['user']['url']


USTREAM_REGEX = re.compile('https?://(www\.)?ustream\.tv/recorded/(?P<id>\d+)')
SUITE = {
    'regex': USTREAM_REGEX,
    'funcs': {
        'link': get_link,
        'title': get_title,
        'description': get_description,
        'flash_enclosure_url': get_flash_enclosure_url,
        'embed': get_embed,
        'thumbnail_url': get_thumbnail_url,
        'publish_date': get_publish_date,
        'tags': get_tags,
        'user': get_user,
        'user_url': get_user_url
        }
    }
