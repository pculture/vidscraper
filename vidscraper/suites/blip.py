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
import re
import urllib
import urlparse

import feedparser
from vidscraper.compat import json
from vidscraper.suites.base import BaseSuite
from vidscraper.utils.feedparser import get_entry_thumbnail_url, \
                                        get_first_accepted_enclosure
from vidscraper.utils.http import clean_description_html


class BlipSuite(BaseSuite):
    regex = re.compile(r'^https?://(?P<subsite>[a-zA-Z]+\.)?blip.tv/')

    api_fields = set(['link', 'title', 'description', 'file_url', 'embed_code',
            'thumbnail_url', 'tags', 'publish_datetime', 'user', 'user_url'])

    oembed_fields = set(['user', 'user_url', 'embed_code', 'thumbnail_url',
            'title'])

    def _actually_parse_feed_entry(self, entry):
        """
        Reusable method to parse a feedparser entry from a blip rss feed into
        a dictionary mapping :class:`.ScrapedVideo` fields to values.

        """
        enclosure = get_first_accepted_enclosure(entry)

        description = entry['blip_puredescription']
        datestamp = datetime.strptime(entry['blip_datestamp'],
                                      "%Y-%m-%dT%H:%M:%SZ")
        data = {
            'link': entry['link'],
            'title': entry['title'],
            'description': clean_description_html(description),
            'file_url': enclosure['url'],
            'embed_code': entry['media_player']['content'],
            'publish_datetime': datestamp,
            'thumbnail_url': get_entry_thumbnail_url(entry),
            'tags': [tag['term'] for tag in entry['tags']
                     if tag['scheme'] is None][1:],
            'user': entry['blip_safeusername'],
            'user_url': entry['blip_showpage']
        }
        return data

    def get_api_url(self, video):
        parsed_url = urlparse.urlparse(video.url)
        post_id = parsed_url[2].rsplit('-', 1)[1]
        new_parsed_url = parsed_url[:2] + ("/rss/%s" % post_id,
                                            None, None, None)
        return urlparse.urlunparse(new_parsed_url)

    def parse_api_response(self, response_text):
        parsed = feedparser.parse(response_text)
        return self._actually_parse_feed_entry(parsed.entries[0])

    def get_oembed_url(self, video):
        return u"http://blip.tv/oembed/?url=%s" % urllib.quote_plus(video.url)

    def parse_oembed_response(self, response_text):
        parsed = json.loads(response_text)
        return {
            'user': parsed['author_name'],
            'user_url': parsed['author_url'],
            'embed_code': parsed['html'],
            'thumbnail_url': parsed['thumbnail_url'],
            'title': parsed['title']
        }

    def get_feed_entries(self, feed_url):
        parsed = feedparser.parse(feed_url)
        return parsed.entries

    def parse_feed_entry(self, entry, fields=None):
        data = self._actually_parse_feed_entry(entry)
        video = self.get_video(data['file_url'], fields)
        for field, value in data.iteritems():
            if field in video.fields:
                setattr(video, field, value)
        return video

    def get_search_results(self, search_string, order_by='relevant', **kwargs):
        # TODO: Add support for ordering.
        get_params = {'q': search_string}
        url = u"http://blip.tv/rss?%s" % urllib.urlencode(get_params)
        return self.get_feed_entries(url)

    def parse_search_result(self, result, fields=None):
        return self.parse_feed_entry(result, fields)
