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

import datetime
import re
import urllib

from lxml import builder
from lxml import etree
from lxml.html import builder as E
from lxml.html import tostring
import simplejson

from vidscraper.decorators import provide_shortmem, parse_url, returns_unicode
from vidscraper import errors
from vidscraper import util


EMaker = builder.ElementMaker()
EMBED = EMaker.embed

EMBED_WIDTH = 425
EMBED_HEIGHT = 344

def parse_api(scraper_func, shortmem=None):
    def new_scraper_func(url, shortmem=None, *args, **kwargs):
        if not shortmem.get('api_data'):
            api_url = 'http://vimeo.com/api/clip/%s.json' % (
                VIMEO_REGEX.match(url).groupdict()['video_id'])
            api_data = simplejson.decode(
                util.open_url_while_lying_about_agent(api_url).read().decode(
                    'utf8'))[0]
            shortmem['api_data'] = api_data
        return scraper_func(url, shortmem=shortmem, *args, **kwargs)
    return new_scraper_func

@provide_shortmem
@parse_url
@returns_unicode
def scrape_title(url, shortmem=None):
    try:
        return shortmem['base_etree'].xpath(
            "id('header')/div/div[@class='title']")[0].text_content().strip()
    except IndexError:
        raise errors.FieldNotFound('Could not find the title field')


@provide_shortmem
@parse_url
@returns_unicode
def scrape_description(url, shortmem=None):
    try:
        return util.clean_description_html(
            util.lxml_inner_html(
                shortmem['base_etree'].xpath(
                    'id("description")')[0]).strip())
    except IndexError:
        raise errors.FieldNotFound('Could not find the description field')


@provide_shortmem
@parse_url
@returns_unicode
def scrape_file_url(url, shortmem=None):
    vimeo_match = VIMEO_REGEX.match(url)
    video_id = vimeo_match.group(2)
    video_data_url = (
        u"http://www.vimeo.com/moogaloop/load/clip:%s" % video_id)
    vimeo_data = None
    for i in range(5):
        try:
            vimeo_data = etree.parse(video_data_url)
        except etree.XMLSyntaxError:
            pass
        else:
            break
    if not vimeo_data:
        return ''
    req_sig = vimeo_data.find('request_signature').text
    req_sig_expires = vimeo_data.find('request_signature_expires').text
    file_url = "http://www.vimeo.com/moogaloop/play/clip:%s/%s/%s/?q=sd" % (
        video_id, req_sig, req_sig_expires)
    shortmem['file_url'] = file_url
    return file_url


@provide_shortmem
def file_url_is_flaky(url, shortmem=None):
    return True


@provide_shortmem
@parse_url
@returns_unicode
def get_flash_enclosure_url(url, shortmem=None):
    vimeo_match = VIMEO_REGEX.match(url)
    video_id = vimeo_match.group(2)
    return 'http://vimeo.com/moogaloop.swf?clip_id=' + video_id


@provide_shortmem
@returns_unicode
def get_embed(url, shortmem=None, width=EMBED_WIDTH, height=EMBED_HEIGHT):
    get_dict = {'server': 'vimeo.com',
                'show_title': 1,
                'show_byline': 1,
                'show_portrait': 0,
                'color': '',
                'fullscreen': 1}

    get_dict['clip_id'] = VIMEO_REGEX.match(url).groupdict()['video_id']

    flash_url = 'http://vimeo.com/moogaloop.swf?' + urllib.urlencode(get_dict)

    object_children = (
        E.PARAM(name="allowfullscreen", value="true"),
        E.PARAM(name="allowscriptaccess", value="always"),
        E.PARAM(name="movie", value=flash_url),
        EMBED(src=flash_url,
              type="application/x-shockwave-flash",
              allowfullscreen="true",
              allowscriptaccess="always",
              width=str(EMBED_WIDTH), height=str(EMBED_HEIGHT)))
    main_object = E.OBJECT(
        width=str(EMBED_WIDTH), height=str(EMBED_HEIGHT), *object_children)

    return tostring(main_object)

@provide_shortmem
@parse_url
@parse_api
@returns_unicode
def get_thumbnail_url(url, shortmem=None):
    return shortmem['api_data'].get('thumbnail_medium')

@provide_shortmem
@parse_url
@parse_api
@returns_unicode
def get_user(url, shortmem=None):
    return shortmem['api_data'].get('user_name')

@provide_shortmem
@parse_url
@parse_api
@returns_unicode
def get_user_url(url, shortmem=None):
    return shortmem['api_data'].get('user_url')


@provide_shortmem
@parse_url
@parse_api
def scrape_publish_date(url, shortmem=None):
    return datetime.datetime.strptime(
        shortmem['api_data']['upload_date'], '%Y-%m-%d %H:%M:%S')



VIMEO_REGEX = re.compile(r'https?://([^/]+\.)?vimeo.com/(?P<video_id>\d+)')
SUITE = {
    'regex': VIMEO_REGEX,
    'funcs': {
        'title': scrape_title,
        'description': scrape_description,
        'publish_date': scrape_publish_date,
        'file_url': scrape_file_url,
        'file_url_is_flaky': file_url_is_flaky,
        'flash_enclosure_url': get_flash_enclosure_url,
        'publish_date': scrape_publish_date,
        'embed': get_embed,
        'thumbnail_url': get_thumbnail_url,
        'user': get_user,
        'user_url': get_user_url},
    'order': ['title', 'description', 'file_url', 'embed']}
            
