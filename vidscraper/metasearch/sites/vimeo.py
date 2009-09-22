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

from datetime import datetime
import md5
import simplejson
import urllib
import urllib2

from vidscraper.metasearch import defaults
from vidscraper.metasearch import util as metasearch_util
from vidscraper.sites import vimeo as vimeo_scraper

VIMEO_QUERY_BASE = 'http://vimeo.com/api/rest/?'

VIMEO_API_KEY = None # set these elsewhere
VIMEO_API_SECRET = None

class VimeoRequest(urllib2.Request):
    def __init__(self, params):
        sorted_args = [VIMEO_API_SECRET]
        for k in sorted(params.keys()):
            sorted_args.append(k + params[k])

        params['api_sig'] = md5.new(''.join(sorted_args)).hexdigest()

        url = VIMEO_QUERY_BASE + urllib.urlencode(params)
        urllib2.Request.__init__(self, url,
                                 headers={
                'User-Agent': 'Miro-Community'})

def parse_entry(entry):
    parsed = {
        'title': entry['title'],
        'description': entry['caption'],
        'link': entry['urls']['url']['_content'],
        'thumbnail_url': entry['thumbnails']['thumbnail'][-1]['_content'],
        'publish_date': datetime.strptime(entry['upload_date'],
                                          '%Y-%m-%d %H:%M:%S'),
        }
    parsed['file_url'] = vimeo_scraper.scrape_file_url(parsed['link'])
    parsed['embed'] = vimeo_scraper.get_embed(parsed['link'])
    if 'tags' in entry:
        parsed['tags'] = [tag['_content'] for tag in entry['tags']['tag']]

    return parsed

def get_entries(include_terms, exclude_terms=None,
                order_by=None, **kwargs):
    search_string = metasearch_util.search_string_from_terms(
        include_terms, exclude_terms)

    get_params = {
        'format': 'json',
        'nojsoncallback': '1',
        'method': 'vimeo.videos.search',
        'query': search_string,
        'per_page': str(defaults.DEFAULT_MAX_RESULTS),
        'fullResponse': '1',
        'api_key': VIMEO_API_KEY
        }

    request = VimeoRequest(get_params)
    fp = urllib2.HTTPHandler().http_open(request)
    json = simplejson.load(fp)


    return [parse_entry(entry) for entry in json['videos']['video']]

SUITE = {
    'id': 'vimeo',
    'display_name': 'Vimeo',
    'order_bys': [],
    'func': get_entries}
