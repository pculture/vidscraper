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

try:
    import oauth2
except ImportError:
    oauth2 = None

from vidscraper.compat import json
from vidscraper.suites import BaseSuite, registry


class VimeoSuite(BaseSuite):
    """
    Suite for vimeo.com. Currently supports their oembed api and simple api. No
    API key is required for this level of access.

    """
    video_regex = r'https?://([^/]+\.)?vimeo.com/(?P<video_id>\d+)'
    feed_regex = r'https?://([^/]+\.)?vimeo.com/'
    _tag_re = re.compile(r'>([\w ]+)</a>')

    api_fields = set(['link', 'title', 'description', 'tags', 'publish_date', 'thumbnail_url', 'user', 'user_url', 'flash_enclosure_url', 'embed_code'])
    oembed_endpoint = u"http://vimeo.com/api/oembed.json"

    def _embed_code_from_id(self, video_id):
        return """<iframe src="http://player.vimeo.com/video/%s" \
width="320" height="240" frameborder="0" webkitAllowFullScreen \
allowFullScreen></iframe>""" % video_id

    def _flash_enclosure_url_from_id(self, video_id):
        return 'http://vimeo.com/moogaloop.swf?clip_id=%s' % video_id

    def get_api_url(self, video):
        video_id = self.video_regex.match(video.url).group('video_id')
        return u"http://vimeo.com/api/v2/video/%s.json" % video_id

    def parse_api_response(self, response_text):
        parsed = json.loads(response_text)[0]
        video_id = parsed['id']
        data = {
            'title': parsed['title'],
            'link': parsed['url'],
            'description': parsed['description'],
            'thumbnail_url': parsed['thumbnail_medium'],
            'user': parsed['user_name'],
            'user_url': parsed['user_url'],
            'publish_date': datetime.strptime(parsed['upload_date'],
                                             '%Y-%m-%d %H:%M:%S'),
            'tags': parsed['tags'].split(', '),
            'flash_enclosure_url': self._flash_enclosure_url_from_id(video_id),
            'embed_code': self._embed_code_from_id(video_id)
        }
        return data

    def parse_feed_entry(self, entry):
        description = entry['summary']
        description, tag_str = description.split("<p><strong>Tags:</strong>")
        tags = [match.group(1) for match in self._tag_re.finditer(tag_str)]
        data = {
            'link': entry['link'],
            'title': entry['title'],
            'description': description,
            'publish_datetime': datetime(*entry['updated_parsed'][:6]),
            'user': entry['author'],
            'user_url': entry['media_credit']['scheme'],
            'thumbnail_url': entry['media_thumbnail'][0]['url'],
            'flash_enclosure_url': entry['media_player']['url'],
            'tags': tags,
        }
        return data

    def get_search_url(self, search_string, order_by=None, **kwargs):
        api_key = kwargs.get('vimeo_api_key')
        if api_key is None:
            raise NotImplementedError("API Key is missing.")
        params = {
            'format': 'json',
            'full_response': '1',
            'method': 'vimeo.videos.search',
            'query': search_string,
        }
        if api_key:
            params['api_key'] = api_key
        if order_by == 'relevant':
            params['sort'] = 'relevant'
        elif order_by == 'latest':
            params['sort'] = 'newest'
        return "http://vimeo.com/api/rest/v2/?%s" % urllib.urlencode(params)

    def get_search_response(self, search_url, **kwargs):
        if oauth2 is None:
            raise NotImplementedError("OAuth2 library must be installed.")
        api_key = kwargs.get('vimeo_api_key')
        api_secret = kwargs.get('vimeo_api_secret')
        if api_key is None or api_secret is None:
            raise NotImplementedError("API Key and Secret missing.")
        consumer = oauth2.Consumer(api_key, api_secret)
        client = oauth2.Client(consumer)
        request = client.request(url)
        return json.loads(request[1])

    def get_search_results(self, search_response):
        return search_response['videos']['video']

    def parse_search_result(self, result):
        # TODO: results have an embed_privacy key. What is this? Should
        # vidscraper return that information? Doesn't youtube have something
        # similar?
        video_id = result['id']
        data = {
            'title': result['title'],
            'link': [u['_content'] for u in result['urls']['url']
                    if u['type'] == 'video'][0],
            'description': result['description'],
            'thumbnail_url': result['thumbnails']['thumbnail'][1]['_content'],
            'user': result['owner']['realname'],
            'user_url': result['owner']['profileurl'],
            'publish_datetime': datetime.strptime(result['upload_date'],
                                             '%Y-%m-%d %H:%M:%S'),
            'tags': [t['_content']
                            for t in result.get('tags', {}).get('tag', [])],
            'flash_enclosure_url': self._flash_enclosure_url_from_id(video_id),
            'embed_code': self._embed_code_from_id(video_id)
        }
        return data
registry.register(VimeoSuite)
