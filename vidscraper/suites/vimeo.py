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
import urllib2
import urlparse

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
    feed_regex = (r'http://(?:www\.)?vimeo\.com/'
                  r'(?:(?P<collection>channel|group)s/)?'
                  r'(?P<name>\w+)'
                  r'(?:/(?P<type>videos|likes))?')
    _tag_re = re.compile(r'>([\w ]+)</a>')

    api_fields = set(['link', 'title', 'description', 'tags', 'guid',
                      'publish_datetime', 'thumbnail_url', 'user', 'user_url',
                      'flash_enclosure_url', 'embed_code'])
    oembed_endpoint = u"http://vimeo.com/api/oembed.json"

    def _embed_code_from_id(self, video_id):
        return u"""<iframe src="http://player.vimeo.com/video/%s" \
width="320" height="240" frameborder="0" webkitAllowFullScreen \
allowFullScreen></iframe>""" % video_id

    def _flash_enclosure_url_from_id(self, video_id):
        return u'http://vimeo.com/moogaloop.swf?clip_id=%s' % video_id

    def get_api_url(self, video):
        video_id = self.video_regex.match(video.url).group('video_id')
        return u"http://vimeo.com/api/v2/video/%s.json" % video_id

    def parse_api_response(self, response_text):
        parsed = json.loads(response_text)[0]
        return self._data_from_api_video(parsed)

    def _data_from_api_video(self, video):
        """
        Takes a video dictionary from a vimeo API response and returns a
        dictionary mapping field names to values.

        """
        video_id = video['id']
        data = {
            'title': video['title'],
            'link': video['url'],
            'description': video['description'],
            'thumbnail_url': video['thumbnail_medium'],
            'user': video['user_name'],
            'user_url': video['user_url'],
            'publish_datetime': datetime.strptime(video['upload_date'],
                                             '%Y-%m-%d %H:%M:%S'),
            'tags': [tag for tag in video['tags'].split(', ') if tag],
            'flash_enclosure_url': self._flash_enclosure_url_from_id(video_id),
            'embed_code': self._embed_code_from_id(video_id),
            'guid': 'tag:vimeo,%s:clip%i' % (video['upload_date'][:10],
                                             video['id'])
        }
        return data

    def _get_user_api_url(self, user, type):
        return 'http://vimeo.com/api/v2/%s/%s.json' % (user, type)
        
    def get_feed_url(self, feed_url, type_override=None):
        """
        Rewrites a feed url into an api request url so that crawl can work, and
        because more information can be retrieved from the api.

        """
        groups = self.feed_regex.match(feed_url).groupdict()
        if groups['collection'] is not None:
            path = "/".join((groups['collection'], groups['name']))
        else:
            path = groups['name']
        return self._get_user_api_url(path,
                                      groups['type']
                                      if not type_override else type_override)

    def get_feed_response(self, feed, feed_url):
        response_text = urllib2.urlopen(feed_url, timeout=5).read()
        return json.loads(response_text)

    def get_feed_info_response(self, feed, response):
        info_url = self.get_feed_url(feed.original_url, type_override='info')
        return self.get_feed_response(feed, info_url)

    def get_feed_title(self, feed, response):
        username = response['display_name']
        if feed.url.endswith('likes.json'):
            return 'Videos %s likes on Vimeo' % username
        else:
            return "%s's videos on Vimeo" % username

    def get_feed_entry_count(self, feed, response):
        if feed.url.endswith('likes.json'):
            return response['total_videos_liked']
        else:
            return response['total_videos_uploaded']

    def get_feed_description(self, feed, response):
        return response['bio']

    def get_feed_webpage(self, feed, response):
        if feed.url.endswith('likes.json'):
            return '%s/likes' % response['profile_url']
        else:
            return response['videos_url']

    def get_feed_thumbnail_url(self, feed, response):
        return response['portrait_huge']

    def get_feed_guid(self, feed, response):
        return None

    def get_feed_last_modified(self, feed, response):
        return None

    def get_feed_etag(self, feed, response):
        return None

    def get_feed_entries(self, feed, feed_response):
        return feed_response

    def parse_feed_entry(self, entry):
        return self._data_from_api_video(entry)

    def get_next_feed_page_url(self, last_url, feed_response):
        # TODO: Vimeo only lets the first 3 pages of 20 results each be fetched
        # with the simple API. If an api key and secret are passed in, this
        # should use the advanced API instead. (Also, it should be possible to
        # pass those in.
        parsed = urlparse.urlparse(last_url)
        params = urlparse.parse_qs(parsed.query)
        try:
            page = int(params.get('page', ['1'])[0])
        except ValueError:
            page = 1
        params['page'] = unicode(page + 1)
        return "%s?%s" % (urlparse.urlunparse(parsed[:4] + (None, None,)),
                          urllib.urlencode(params, True))

    def get_search_url(self, search, order_by=None, extra_params=None):
        if search.api_keys is None or not search.api_keys.get('vimeo_api_key'):
            raise NotImplementedError("API Key is missing.")
        params = {
            'format': 'json',
            'full_response': '1',
            'method': 'vimeo.videos.search',
            'query': search.query,
        }
        params['api_key'] = search.api_keys['vimeo_api_key']
        if order_by == 'relevant':
            params['sort'] = 'relevant'
        elif order_by == 'latest':
            params['sort'] = 'newest'
        if extra_params is not None:
            params.update(extra_params)
        return "http://vimeo.com/api/rest/v2/?%s" % urllib.urlencode(params)

    def get_next_search_page_url(self, search, search_response,
                                 order_by=None):
        total = int(search_response['total'])
        page = int(search_response['page'])
        per_page = int(search_response['per_page'])
        if page * per_page > total:
            return None
        extra_params = {'page': page + 1}
        return self.get_search_url(search, order_by,
                                   extra_params=extra_params)

    def get_search_response(self, search, search_url):
        if oauth2 is None:
            raise NotImplementedError("OAuth2 library must be installed.")
        api_key = (search.api_keys.get('vimeo_api_key')
                   if search.api_keys else None)
        api_secret = (search.api_keys.get('vimeo_api_secret')
                      if search.api_keys else None)
        if api_key is None or api_secret is None:
            raise NotImplementedError("API Key and Secret missing.")
        consumer = oauth2.Consumer(api_key, api_secret)
        client = oauth2.Client(consumer)
        request = client.request(search_url)
        return json.loads(request[1])

    def get_search_results(self, search, search_response):
        return search_response['videos']['video']

    def parse_search_result(self, search, result):
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
