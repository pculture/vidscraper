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

import re
import urllib

import feedparser
# add the OpenSearch namespace to FeedParser
# http://code.google.com/p/feedparser/issues/detail?id=55
feedparser._FeedParserMixin.namespaces[
    'http://a9.com/-/spec/opensearch/1.1/'] = 'opensearch'

from vidscraper.suites import BaseSuite, registry
from vidscraper.utils.feedparser import get_entry_thumbnail_url
from vidscraper.utils.feedparser import struct_time_to_datetime

class YouTubeSuite(BaseSuite):
    video_regex = r'^https?://(' +\
    r'([^/]+\.)?youtube.com/(?:watch)?\?(\w+=[^&]+&)*v=' +\
                  r'|youtu.be/)(?P<video_id>[\w-]+)'
    feed_regex = r'^https?://([^/]+\.)?youtube.com/'
    non_feed_regexes = [re.compile(r) for r in (
            (r'^(http://)?(www\.)?youtube\.com/profile(_videos)?'
             r'\?(\w+=\w+&)*user=(?P<name>\w+)'),
            (r'^(http://)?(www\.)?youtube\.com/((rss/)?user/)?'
             r'(?P<name>\w+)'))]
    feed_url_base = ('http://gdata.youtube.com/feeds/base/users/%s/'
                    'uploads?alt=rss&v=2')

    oembed_endpoint = "http://www.youtube.com/oembed"
    api_fields = set(['link', 'title', 'description',
                      'thumbnail_url', 'publish_datetime', 'tags',
                      'flash_enclosure_url', 'user', 'user_url'])

    def get_feed_url(self, url, extra_params=None):
        for regex in self.non_feed_regexes:
            match = regex.match(url)
            if match:
                name = match.group('name')
                url = self.feed_url_base % name
                break
        if extra_params:
            url = '%s&%s' % (url, urllib.urlencode(extra_params))
        return url

    def parse_feed_entry(self, entry):
        """
        Reusable method to parse a feedparser entry from a youtube rss feed.
        Returns a dictionary mapping :class:`.ScrapedVideo` fields to values.

        """
        user = entry['author']
        if 'published_parsed' in entry:
            best_date = struct_time_to_datetime(entry['published_parsed'])
        elif 'updated_parsed' in entry:
            best_date = struct_time_to_datetime(entry['updated_parsed'])
        else:
            best_date = None
        data = {
            'link': entry['links'][0]['href'].split('&', 1)[0],
            'title': entry['title'],
            'description': entry['summary'],
            'thumbnail_url': get_entry_thumbnail_url(entry),
            'publish_datetime': best_date,
            'tags': [t['term'] for t in entry['tags']
                    if not t['term'].startswith('http')],
            'user': user,
            'user_url': u'http://www.youtube.com/user/%s' % user,
        }
        if 'guid' in entry.keys():
            data['guid'] = entry.guid
        if 'media_player' in entry: # not in feeds, just the API
            data['flash_enclosure_url'] = entry['media_player']['url']
        return data

    def get_feed_entry_count(self, feed, feed_response):
        return int(feed_response.feed.get('opensearch_totalresults',
                                          len(feed_response.entries)))

    def get_api_url(self, video):
        video_id = self.video_regex.match(video.url).group('video_id')
        return "http://gdata.youtube.com/feeds/api/videos/%s" % video_id

    def parse_api_response(self, response_text):
        parsed = feedparser.parse(response_text)
        return self.parse_feed_entry(parsed.entries[0])

    def get_search_url(self, search_string, order_by=None, extra_params=None,
                       **kwargs):
        params = {
            'vq': search_string,
        }
        if extra_params is not None:
            params.update(extra_params)
        if order_by == 'relevant':
            params['orderby'] = 'relevance'
        elif order_by == 'latest':
            params['orderby'] = 'published'
        return 'http://gdata.youtube.com/feeds/api/videos?%s' % (
                                    urllib.urlencode(params))

    def get_next_page_url_params(self, response):
        start_index = response['feed'].get('opensearch_startindex', None)
        per_page = response['feed'].get('opensearch_itemsperpage', None)
        total_results = response['feed'].get('opensearch_totalresults', None)
        if start_index is None or per_page is None or total_results is None:
            return None
        new_start = int(start_index) + int(per_page)
        if new_start > int(total_results):
            return None
        extra_params = {
            'start-index': new_start,
            'max-results': per_page
        }
        return extra_params

    def get_next_search_page_url(self, search, search_response,
                                 order_by=None, **kwargs):
        extra_params = self.get_next_page_url_params(search_response)
        if not extra_params:
            return None
        return self.get_search_url(
            search.query, order_by,
            extra_params=extra_params,
            **kwargs)

    def get_next_feed_page_url(self, feed, feed_response):
        extra_params = self.get_next_page_url_params(feed_response)
        if not extra_params:
            return None
        return self.get_feed_url(feed.url, extra_params=extra_params)

registry.register(YouTubeSuite)
