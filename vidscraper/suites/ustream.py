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

from vidscraper.compat import json
from vidscraper.suites import BaseSuite, registry


class UstreamSuite(BaseSuite):
    """Suite for fetching data on ustream videos."""
    # TODO: Ustream has feeds and search functionality - add support for that!
    video_regex = 'https?://(www\.)?ustream\.tv/recorded/(?P<id>\d+)'

    oembed_endpoint = "http://www.ustream.tv/oembed/"

    api_fields = set(['link', 'title', 'description', 'flash_enclosure_url',
                      'embed_code', 'thumbnail_url', 'publish_date', 'tags',
                      'user', 'user_url'])

    def get_api_url(self, video):
        video_id = self.video_regex.match(video.url).group('id')
        if video.api_keys is None or 'ustream_key' not in video.api_keys:
            raise ValueError("API key must be set for Ustream API requests.")
        return 'http://api.ustream.tv/json/video/%s/getInfo/?key=%s' % (
                                video_id, video.api_keys['ustream_key'])

    def parse_api_response(self, response_text):
        parsed = json.loads(response_text)['results']
        url = parsed['embedTagSourceUrl']
        publish_date = datetime.datetime.strptime(parsed['createdAt'],
                                                 '%Y-%m-%d %H:%M:%S')
        data = {
            'link': parsed['url'],
            'title': parsed['title'],
            'description': parsed['description'],
            'flash_enclosure_url': url,
            'embed_code': "<iframe src='%s' width='320' height='260' />" % url,
            'thumbnail_url': parsed['imageUrl']['medium'],
            'publish_date': publish_date,
            'tags': [unicode(tag) for tag in parsed['tags']],
            'user': parsed['user']['userName'],
            'user_url': parsed['user']['url']
        }
        return data
registry.register(UstreamSuite)
