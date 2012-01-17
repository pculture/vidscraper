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
import urllib
import urlparse

import feedparser

from vidscraper.suites import BaseSuite, registry
from vidscraper.utils.feedparser import get_entry_thumbnail_url, \
                                        get_first_accepted_enclosure
from vidscraper.utils.http import clean_description_html


class BlipSuite(BaseSuite):
    video_regex = r'^https?://(?P<subsite>[a-zA-Z]+\.)?blip.tv(?:/.*)?(?<!.mp4)$'
    feed_regex = video_regex

    api_fields = set(['guid', 'link', 'title', 'description', 'file_url',
                      'embed_code', 'thumbnail_url', 'tags',
                      'publish_datetime', 'user', 'user_url', 'license'])

    oembed_endpoint = u"http://blip.tv/oembed/"
    oembed_fields = set(['user', 'user_url', 'embed_code', 'thumbnail_url',
            'title'])

    def get_feed_url(self, url):
        if not url.endswith('/rss'):
            if url.endswith('/'):
                return url + 'rss'
            else:
                return url + '/rss'
        return url

    def parse_feed_entry(self, entry):
        """
        Reusable method to parse a feedparser entry from a blip rss feed into
        a dictionary mapping :class:`.Video` fields to values.

        """
        enclosure = get_first_accepted_enclosure(entry)

        data = {
            'guid': entry['id'],
            'link': entry['link'],
            'title': entry['title'],
            'description': clean_description_html(
                entry['blip_puredescription']),
            'file_url': enclosure['url'],
            'embed_code': entry['media_player']['content'],
            'publish_datetime': datetime.strptime(entry['blip_datestamp'],
                                                  "%Y-%m-%dT%H:%M:%SZ"),
            'thumbnail_url': get_entry_thumbnail_url(entry),
            'tags': [tag['term'] for tag in entry['tags']
                     if tag['scheme'] is None][1:],
            'user': entry['blip_safeusername'],
            'user_url': entry['blip_showpage']
        }
        if 'license' in entry:
            data['license'] = entry['license']
        return data

    def get_next_feed_page_url(self, feed, feed_response):
        parsed = urlparse.urlparse(feed_response.href)
        params = urlparse.parse_qs(parsed.query)
        try:
            page = int(params.get('page', ['1'])[0])
        except ValueError:
            page = 1
        params['page'] = unicode(page + 1)
        return "%s?%s" % (urlparse.urlunparse(parsed[:4] + (None, None)),
                          urllib.urlencode(params, True))

    def get_api_url(self, video):
        if '-' not in video.url:
            # http://blip.tv/file/1077145/
            # oh no, an older URL; get the redirected URL
            resp = urllib.urlopen(video.url)
            video.url = resp.geturl()
            resp.close()
        parsed_url = urlparse.urlparse(video.url)
        post_id = parsed_url[2].rsplit('-', 1)[1]
        new_parsed_url = parsed_url[:2] + ("/rss/%s" % post_id,
                                            None, None, None)
        return urlparse.urlunparse(new_parsed_url)

    def parse_api_response(self, response_text):
        parsed = feedparser.parse(response_text)
        return self.parse_feed_entry(parsed.entries[0])
registry.register(BlipSuite)
