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

import urllib

import feedparser

from vidscraper.sites import youtube as youtube_scraper
from vidscraper.metasearch import defaults
from vidscraper.metasearch import util as metasearch_util

#'http://gdata.youtube.com/feeds/api/videos?vq=%s&amp;alt=rss'
YOUTUBE_QUERY_BASE = 'http://gdata.youtube.com/feeds/api/videos'


def parse_youtube_entry(entry):
    shortmem = {'parsed_entry': entry}
    parsed_entry = {}
    link = entry['link']
    if '&amp;' in link:
        # Feedparser doesn't always parse these into &s
        link = link.replace('&amp;', '&')
    for field, func in youtube_scraper.SUITE['funcs'].items():
        parsed_entry[field] = func(link, shortmem)

    return parsed_entry


def get_entries(include_terms, exclude_terms=None,
                order_by='relevant', **kwargs):

    search_string = metasearch_util.search_string_from_terms(
        include_terms, exclude_terms)

    # Note here that we can use more than 50
    # (metasearch.DEFAULT_MAX_RESULTS), but that requires doing multiple
    # queries for RSS "pagination" with youtube's API.  Maybe we should
    # implement that later.
    get_params = {
        'vq': search_string.encode('utf8'),
        'alt': 'rss',
        'max-results': defaults.DEFAULT_MAX_RESULTS}

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
