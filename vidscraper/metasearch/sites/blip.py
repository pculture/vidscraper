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

from vidscraper.metasearch import util as metasearch_util
from vidscraper.sites import blip as blip_scraper

#'http://www.blip.tv/search/?search=(string)skin=rss'
BLIP_QUERY_BASE = 'http://blip.tv/search/'


def parse_entry(entry):
    shortmem = {'feed_item': entry}
    parsed_entry = {}
    for field, func in blip_scraper.SUITE['funcs'].items():
        parsed_entry[field] = func(entry['link'], shortmem)

    return parsed_entry


def get_entries(include_terms, exclude_terms=None,
                order_by='relevant', **kwargs):
    search_string = metasearch_util.search_string_from_terms(
        include_terms, exclude_terms)

    get_params = {
        'skin': 'rss',
        'search': search_string.encode('utf8')}

    if order_by == 'latest':
        get_params['sort'] = 'date'

    get_url = '%s?%s' % (BLIP_QUERY_BASE, urllib.urlencode(get_params))

    parsed_feed = feedparser.parse(get_url)

    if len(parsed_feed.entries) == 1 and \
            parsed_feed.entries[0].summary == 'Search returned no results.':
        return [] # no results

    return [parse_entry(entry) for entry in parsed_feed.entries]


SUITE = {
    'id': 'blip',
    'display_name': 'Blip.Tv',
    'order_bys': ['latest', 'relevant'],
    'func': get_entries}
