# Miro - an RSS based video player application
# Copyright 2009 - Participatory Culture Foundation
# 
# This file is part of vidscraper.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import cgi
import re
import urlparse

import feedparser

from lxml import builder
from lxml.html import builder as E
from lxml.html import tostring

from vidscraper.decorators import (provide_shortmem,
                                   returns_unicode, returns_struct_time)


EMaker = builder.ElementMaker()
EMBED = EMaker.embed

EMBED_WIDTH = 425
EMBED_HEIGHT = 344

def canonical_url(url):
    """
    Return the canonical URL for a given YouTube URL.  This strips off any
    trailing &feature= nonsense.
    """
    if '&feature=' in url:
        start = url.find('&feature=')
        end = url.find('&', start+1)
        if end != -1:
            return url[:start] + url[end:]
        else:
            url = url[:start]
    return url

def provide_api(func):
    """
    A quick decorator to provide the scraped YouTube API data for the video.
    """
    def wrapper(url, shortmem=None):
        if shortmem.get('parsed_feed') is None:
            video_id = cgi.parse_qs(urlparse.urlsplit(url)[3])['v'][0]
            api_url = 'http://gdata.youtube.com/feeds/api/videos/' + video_id
            feed = feedparser.parse(api_url)
            shortmem['parsed_feed'] = feed
        return func(url, shortmem)
    return wrapper

@provide_shortmem
@provide_api
@returns_unicode
def get_link(url, shortmem=None):
    return canonical_url(shortmem['parsed_feed'].entries[0].link)

@provide_shortmem
@provide_api
@returns_unicode
def scrape_title(url, shortmem=None):
    return shortmem['parsed_feed'].entries[0].title

@provide_shortmem
@provide_api
@returns_unicode
def scrape_description(url, shortmem=None):
    entry = shortmem['parsed_feed'].entries[0]
    if 'media_description' in entry:
        return entry.media_description
    else:
        return entry.description

@provide_shortmem
@returns_unicode
def get_embed(url, shortmem=None, width=EMBED_WIDTH, height=EMBED_HEIGHT):
    video_id = cgi.parse_qs(urlparse.urlsplit(url)[3])['v'][0]

    flash_url = 'http://www.youtube.com/v/%s&hl=en&fs=1' % video_id

    object_children = (
        E.PARAM(name="movie", value=flash_url),
        E.PARAM(name="allowFullScreen", value="true"),
        E.PARAM(name="allowscriptaccess", value="always"),
        EMBED(src=flash_url,
              type="application/x-shockwave-flash",
              allowfullscreen="true",
              allowscriptaccess="always",
              width=str(EMBED_WIDTH), height=str(EMBED_HEIGHT)))
    main_object = E.OBJECT(
        width=str(EMBED_WIDTH), height=str(EMBED_HEIGHT), *object_children)

    return tostring(main_object)


@provide_shortmem
@returns_unicode
def get_flash_enclosure_url(url, shortmem=None):
    return canonical_url(url)


@provide_shortmem
@returns_unicode
def get_thumbnail_url(url, shortmem=None):
    video_id = cgi.parse_qs(urlparse.urlsplit(url)[3])['v'][0]
    return 'http://img.youtube.com/vi/%s/hqdefault.jpg' % video_id


@provide_shortmem
@provide_api
@returns_struct_time
def scrape_published_date(url, shortmem=None):
    if not shortmem['parsed_feed'].entries:
        return
    return shortmem['parsed_feed'].entries[0].published_parsed


@provide_shortmem
@provide_api
def get_tags(url, shortmem=None):
    if not shortmem['parsed_feed'].entries:
        return
    return [tag['term'] for tag in shortmem['parsed_feed'].entries[0].tags
            if tag['scheme'] != 'http://schemas.google.com/g/2005#kind']


@provide_shortmem
@provide_api
def get_user(url, shortmem=None):
    if not shortmem['parsed_feed'].entries:
        return ''
    return shortmem['parsed_feed'].entries[0]['author']

@provide_shortmem
@provide_api
def get_user_url(url, shortmem=None):
    if not shortmem['parsed_feed'].entries:
        return ''
    return 'http://www.youtube.com/user/%s' % (
        shortmem['parsed_feed'].entries[0]['author'],)

YOUTUBE_REGEX = re.compile(r'https?://([^/]+\.)?youtube.com/(?:watch)?\?v=')
SUITE = {
    'regex': YOUTUBE_REGEX,
    'funcs': {
        'link': get_link,
        'title': scrape_title,
        'description': scrape_description,
        'embed': get_embed,
        'thumbnail_url': get_thumbnail_url,
        'publish_date': scrape_published_date,
        'tags': get_tags,
        'flash_enclosure_url': get_flash_enclosure_url,
        'user': get_user,
        'user_url': get_user_url}}
