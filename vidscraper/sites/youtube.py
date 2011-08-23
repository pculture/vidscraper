# -*- test-case-name: vidscraper.tests.test_youtube -*-
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
import datetime
import re
import urlparse
import urllib2

from lxml import etree

from vidscraper.decorators import provide_shortmem, returns_unicode
from vidscraper.errors import BaseUrlLoadFailure, VideoDeleted

EMBED_WIDTH = 480
EMBED_HEIGHT = 390

def canonical_url(url):
    """
    Return the canonical URL for a given YouTube URL.  This strips off any
    trailing &feature= nonsense.
    """
    if '://youtu.be/' in url:
        url = url.replace('://youtu.be/', '://www.youtube.com/watch?v=')
    if '&amp;' in url:
        url = url.replace('&amp;', '&')
    scheme, netloc, path, params, query, fragment = urlparse.urlparse(url)
    return '%s://%s%s?v=%s' % (scheme, netloc, path,
                               urlparse.parse_qs(query)['v'][0])

def get_video_id(url, shortmem=None):
    if 'video_id' not in shortmem:
        parts = urlparse.urlsplit(url)
        if parts.netloc == 'youtu.be': # short URL
            video_id = parts.path[1:]
        else:
            video_id = cgi.parse_qs(parts.query)['v'][0]
        shortmem['video_id'] = video_id
    return shortmem['video_id']
            
def provide_api(func):
    """
    A quick decorator to provide the scraped YouTube API data for the video.
    """
    def wrapper(url, shortmem=None, *args, **kwargs):
        if shortmem.get('base_etree') is None:
            video_id = get_video_id(url, shortmem)
            api_url = 'http://gdata.youtube.com/feeds/api/videos/%s?v=2' % (
                video_id,)
            try:
                api_request = urllib2.urlopen(api_url)
            except urllib2.HTTPError, e:
                if 400 <= e.code < 500:
                    try:
                        root = etree.parse(e)
                    except Exception, e:
                        raise BaseUrlLoadFailure(e)
                    else:
                        data = root.findtext(
                            './/{http://schemas.google.com/g/2005}'
                            'internalReason')
                        if ((e.code == 403 and data == 'Private video') or
                            (e.code == 404 and data == 'Video not found')):
                            raise VideoDeleted(data)
                else:
                    data = e.read()
                raise BaseUrlLoadFailure('status %s: %s' % (e.code,
                                                            data))
            else:
                try:
                    root = etree.parse(api_request)
                except Exception, e:
                    raise BaseUrlLoadFailure(e)
                else:
                    shortmem['base_etree'] = root

        return func(url, shortmem, *args, **kwargs)
    return wrapper

@returns_unicode
def get_link(url, shortmem=None):
    return canonical_url(url)

@provide_shortmem
@provide_api
@returns_unicode
def scrape_title(url, shortmem=None):
    root = shortmem['base_etree']
    return root.findtext('{http://www.w3.org/2005/Atom}title')

@provide_shortmem
@provide_api
@returns_unicode
def scrape_description(url, shortmem=None):
    root = shortmem['base_etree']
    return root.findtext('.//{http://search.yahoo.com/mrss/}description')

@provide_shortmem
@provide_api
@returns_unicode
def get_embed(url, shortmem=None, width=None, height=None,
              use_widescreen=False):
    if (width is None and height is None):
        height = EMBED_HEIGHT
        if use_widescreen:
            root = shortmem['base_etree']
            if root.findtext(
                './/{http://gdata.youtube.com/schemas/2007}aspectRatio'):
                width = 640
            else:
                width = 480
        else:
            width = EMBED_WIDTH

    return ('<iframe width="%d" height="%d" src="'
            'http://www.youtube.com/embed/%s" frameborder="0" allowfullscreen>'
            '</iframe>') % (width, height, get_video_id(url, shortmem))

@provide_shortmem
@returns_unicode
def get_flash_enclosure_url(url, shortmem=None):
    return canonical_url(url)


@provide_shortmem
@returns_unicode
def get_thumbnail_url(url, shortmem=None):
    return 'http://img.youtube.com/vi/%s/hqdefault.jpg' % (
        get_video_id(url, shortmem))


@provide_shortmem
@provide_api
def scrape_published_date(url, shortmem=None):
    root = shortmem['base_etree']
    if not root:
        return
    published = root.findtext('{http://www.w3.org/2005/Atom}published')
    if published:
        return datetime.datetime.strptime(published[:19],
                                          '%Y-%m-%dT%H:%M:%S')
    updated = root.findtext('{http://www.w3.org/2005/Atom}updated')
    if updated:
        return datetime.datetime.strptime(updated[:19],
                                          '%Y-%m-%dT%H:%M:%S')

@provide_shortmem
@provide_api
def get_tags(url, shortmem=None):
    root = shortmem['base_etree']
    tags = root.findall('{http://www.w3.org/2005/Atom}category')
    return [(isinstance(tag.attrib['term'], unicode) and tag.attrib['term'])
            or tag.attrib['term'].decode('utf8')
            for tag in tags
            if tag.attrib['term'] and tag.attrib.get('scheme', '').startswith(
            'http://gdata.youtube.com/schemas/2007/')]


@provide_shortmem
@provide_api
def get_user(url, shortmem=None):
    root = shortmem['base_etree']
    return root.findtext('.//{http://www.w3.org/2005/Atom}author/'
                         '{http://www.w3.org/2005/Atom}name')

@provide_shortmem
@provide_api
def get_user_url(url, shortmem=None):
    root = shortmem['base_etree']    
    author = root.findtext('.//{http://www.w3.org/2005/Atom}author/'
                           '{http://www.w3.org/2005/Atom}name')

    return 'http://www.youtube.com/user/%s' % (author,)

@provide_shortmem
@provide_api
def is_embedable(url, shortmem=None):
    root = shortmem['base_etree']
    return root.find(
        '{http://gdata.youtube.com/schemas/2007}noembed') is None

YOUTUBE_REGEX = re.compile(
    r'https?://(([^/]+\.)?youtube.com/(?:watch)?\?(\w+=\w+&)*v=|youtu.be)')
SUITE = {
    'regex': YOUTUBE_REGEX,
    'funcs': {
        'link': get_link,
        'title': scrape_title,
        'description': scrape_description,
        'embed': get_embed,
        'is_embedable': is_embedable,
        'thumbnail_url': get_thumbnail_url,
        'publish_date': scrape_published_date,
        'tags': get_tags,
        'flash_enclosure_url': get_flash_enclosure_url,
        'user': get_user,
        'user_url': get_user_url}}
