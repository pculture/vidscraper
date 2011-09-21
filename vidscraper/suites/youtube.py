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
import urllib

import feedparser

from vidscraper.suites import BaseSuite, registry
from vidscraper.utils.feedparser import get_entry_thumbnail_url


class YouTubeSuite(BaseSuite):
    video_regex = r'^https?://(' +\
    r'([^/]+\.)?youtube.com/(?:watch)?\?(\w+=[^&]+&)*v=' +\
                  r'|youtu.be/)(?P<video_id>\w+)'
    feed_regex = r'^https?://([^/]+\.)?youtube.com/'

    oembed_endpoint = "http://www.youtube.com/oembed"
    api_fields = set(['link', 'title', 'description',
                      'thumbnail_url', 'publish_datetime', 'tags',
                      'flash_enclosure_url', 'user', 'user_url'])

    def _actually_parse_feed_entry(self, entry):
        """
        Reusable method to parse a feedparser entry from a youtube rss feed.
        Returns a dictionary mapping :class:`.ScrapedVideo` fields to values.

        """
        user = entry['author']
        data = {
            'link': entry['links'][0]['href'].split('&', 1)[0],
            'title': entry['title'],
            'description': entry['summary'],
            'thumbnail_url': get_entry_thumbnail_url(entry),
            'publish_datetime': datetime.datetime(*entry['published_parsed'][:6]),
            'tags': [t['term'] for t in entry['tags']
                    if not t['term'].startswith('http')],
            'flash_enclosure_url': entry['media_content'][0]['url'],
            'user': user,
            'user_url': u'http://www.youtube.com/user/%s' % user,
        }
        return data

    def get_api_url(self, video):
        video_id = self.video_regex.match(video.url).group('video_id')
        return "http://gdata.youtube.com/feeds/api/videos/%s" % video_id

    def parse_api_response(self, response_text):
        parsed = feedparser.parse(response_text)
        return self._actually_parse_feed_entry(parsed.entries[0])

    def get_search_results(self, search_string, order_by='relevant', **kwargs):
        params = {
            'vq': search_string,
            #'alt': 'rss' # Default is atom. Does that work?
        }
        if order_by == 'relevant':
            params['orderby'] = 'relevance'
        elif order_by == 'latest':
            params['orderby'] = 'published'
        url = 'http://gdata.youtube.com/feeds/api/videos?%s' % urllib.urlencode(
                                                                params)
        parsed = feedparser.parse_feed(url)
        return parsed.entries

    def parse_search_result(self, result, fields=None):
        data = self._actually_parse_feed_entry(result)
        video = self.get_video(data['link'], fields)
        for field, value in data.iteritems():
            if field in video.fields:
                setattr(video, field, value)
        return video
registry.register(YouTubeSuite)
