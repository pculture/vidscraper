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

import time
from datetime import datetime
from xml.dom import minidom
import re
import urllib
import urllib2
import urlparse

try:
    import oauth2
except ImportError:
    oauth2 = None

from vidscraper.compat import json
from vidscraper.errors import VideoDeleted
from vidscraper.suites import BaseSuite, registry

from vidscraper.utils.feedparser import struct_time_to_datetime
from vidscraper.utils.http import open_url_while_lying_about_agent

LAST_URL_CACHE = "_vidscraper_last_url"

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
    api_regex = (r'http://(?:www\.)?vimeo.com/api/v./'
                 r'(?:(?P<collection>channel|group)s/)?'
                 r'(?P<name>\w+)'
                 r'(?:/(?P<type>videos|likes))\.json')
    _tag_re = re.compile(r'>([\w ]+)</a>')

    api_fields = set(['link', 'title', 'description', 'tags', 'guid',
                      'publish_datetime', 'thumbnail_url', 'user', 'user_url',
                      'flash_enclosure_url', 'embed_code'])
    scrape_fields = set(['link', 'title', 'user', 'user_url', 'thumbnail_url',
                         'embed_code', 'file_url', 'file_url_mimetype',
                         'file_url_expires'])
    oembed_endpoint = u"http://vimeo.com/api/oembed.json"

    def __init__(self, *args, **kwargs):
        super(VimeoSuite, self).__init__(*args, **kwargs)
        self.api_regex = re.compile(self.api_regex)

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

    def get_scrape_url(self, video):
        video_id = self.video_regex.match(video.url).group('video_id')
        return u"http://www.vimeo.com/moogaloop/load/clip:%s" % video_id

    def parse_scrape_response(self, response_text):
        doc = minidom.parseString(response_text)
        error_id = doc.getElementsByTagName('error_id').item(0)
        if (error_id is not None and
            error_id.firstChild.data == 'embed_blocked'):
            return {
                'is_embedable': False
                }
        xml_data = {}
        for key in ('url', 'caption', 'thumbnail', 'uploader_url',
                    'uploader_display_name', 'isHD', 'embed_code',
                    'request_signature', 'request_signature_expires',
                    'nodeId'):
            item = doc.getElementsByTagName(key).item(0)
            str_data = item.firstChild.data
            if isinstance(str_data, unicode):
                xml_data[key] = str_data # actually Unicode
            else:
                xml_data[key] = str_data.decode('utf8')

        data = {
            'link': xml_data['url'],
            'user': xml_data['uploader_display_name'],
            'user_url': xml_data['uploader_url'],
            'title': xml_data['caption'],
            'thumbnail_url': xml_data['thumbnail'],
            'embed_code': xml_data['embed_code'],
            'file_url_expires': struct_time_to_datetime(time.gmtime(
                    int(xml_data['request_signature_expires']))),
            'file_url_mimetype': u'video/x-flv',
            }
        base_file_url = (
            'http://www.vimeo.com/moogaloop/play/clip:%(nodeId)s/'
            '%(request_signature)s/%(request_signature_expires)s'
            '/?q=' % xml_data)
        if xml_data['isHD'] == '1':
            data['file_url'] = base_file_url + 'hd'
        else:
            data['file_url'] = base_file_url + 'sd'

        return data


    def _get_user_api_url(self, user, type):
        return 'http://vimeo.com/api/v2/%s/%s.json' % (user, type)

    def get_feed_url(self, feed_url, type_override=None):
        """
        Rewrites a feed url into an api request url so that crawl can work, and
        because more information can be retrieved from the api.

        """
        match = self.api_regex.match(feed_url)
        if match:
            groups = match.groupdict()
        else:
            groups = self.feed_regex.match(feed_url).groupdict()
        if groups['collection'] is not None:
            path = "/".join((groups['collection'], groups['name']))
        else:
            path = groups['name']
        if type_override:
            type_ = type_override
        elif groups['type']:
            type_ = groups['type']
        else:
            type_ = 'videos'
        return self._get_user_api_url(path, type_)

    def get_feed_response(self, feed, feed_url):
        # NB: for urllib2, Vimeo always returns the first page, so use the
        # lying agent when requesting pages.

        # XXX: we could use the lying agent for everything, but I'd rather let
        # them know that people are using Python to access their API.
        if '?page=' in feed_url:
            response = open_url_while_lying_about_agent(feed_url)
        else:
            response = urllib2.urlopen(feed_url, timeout=5)
        response_text = response.read()
        try:
            return json.loads(response_text)
        except ValueError:
            return None

    def get_feed_info_response(self, feed, response):
        info_url = self.get_feed_url(feed.original_url, type_override='info')
        return self.get_feed_response(feed, info_url)

    def get_feed_title(self, feed, response):
        if 'creator_display_name' in response:
            return u'%s on Vimeo' % response['creator_display_name']
        username = response['display_name']
        if feed.url.endswith('likes.json'):
            return 'Videos %s likes on Vimeo' % username
        else:
            return "%s's videos on Vimeo" % username

    def get_feed_entry_count(self, feed, response):
        if feed.url.endswith('likes.json'):
            return response['total_videos_liked']
        elif 'total_videos_uploaded' in response:
            return response['total_videos_uploaded']
        else:
            return response['total_videos']

    def get_feed_description(self, feed, response):
        if 'bio' in response:
            return response['bio']
        else:
            return response['description']

    def get_feed_webpage(self, feed, response):
        if feed.url.endswith('likes.json'):
            return '%s/likes' % response['profile_url']
        elif 'videos_url' in response:
            return response['videos_url']
        else:
            return response['creator_url']

    def get_feed_thumbnail_url(self, feed, response):
        if 'portrait_huge' in response:
            return response['portrait_huge']
        else:
            return response['logo']

    def get_feed_guid(self, feed, response):
        return None

    def get_feed_last_modified(self, feed, response):
        return None

    def get_feed_etag(self, feed, response):
        return None

    def get_feed_entries(self, feed, feed_response):
        if feed_response is None: # no more data
            return []
        return feed_response

    def parse_feed_entry(self, entry):
        return self._data_from_api_video(entry)

    def get_next_feed_page_url(self, feed, feed_response):
        # TODO: Vimeo only lets the first 3 pages of 20 results each be fetched
        # with the simple API. If an api key and secret are passed in, this
        # should use the advanced API instead. (Also, it should be possible to
        # pass those in.

        # NB: LAST_URL_CACHE is a hack since the current page URL isn't
        # available in the feed_response.  feed.url isn't updated when we're
        # iterating through the feed, so we keep track of it ourselves.
        url = getattr(feed, LAST_URL_CACHE, feed.url)
        parsed = urlparse.urlparse(url)
        params = urlparse.parse_qs(parsed.query)
        try:
            page = int(params.get('page', ['1'])[0])
        except ValueError:
            page = 1
        params['page'] = unicode(page + 1)
        next_url = "%s?%s" % (urlparse.urlunparse(parsed[:4] + (None, None,)),
                          urllib.urlencode(params, True))
        setattr(feed, LAST_URL_CACHE, next_url)
        return next_url


    def get_search_url(self, search, extra_params=None):
        if search.api_keys is None or not search.api_keys.get('vimeo_key'):
            raise NotImplementedError("API Key is missing.")
        params = {
            'format': 'json',
            'full_response': '1',
            'method': 'vimeo.videos.search',
            'query': search.query,
        }
        params['api_key'] = search.api_keys['vimeo_key']
        if search.order_by == 'relevant':
            params['sort'] = 'relevant'
        elif search.order_by == 'latest':
            params['sort'] = 'newest'
        if extra_params is not None:
            params.update(extra_params)
        return "http://vimeo.com/api/rest/v2/?%s" % urllib.urlencode(params)

    def get_next_search_page_url(self, search, search_response):
        total = self.get_search_total_results(search, search_response)
        page = int(search_response['videos']['page'])
        per_page = int(search_response['videos']['perpage'])
        if page * per_page > total:
            return None
        extra_params = {'page': page + 1}
        return self.get_search_url(search,
                                   extra_params=extra_params)

    def get_search_response(self, search, search_url):
        if oauth2 is None:
            raise NotImplementedError("OAuth2 library must be installed.")
        api_key = (search.api_keys.get('vimeo_key')
                   if search.api_keys else None)
        api_secret = (search.api_keys.get('vimeo_secret')
                      if search.api_keys else None)
        if api_key is None or api_secret is None:
            raise NotImplementedError("API Key and Secret missing.")
        consumer = oauth2.Consumer(api_key, api_secret)
        client = oauth2.Client(consumer)
        request = client.request(search_url)
        return json.loads(request[1])

    def get_search_total_results(self, search, search_response):
        if 'videos' not in search_response:
            return 0
        return int(search_response['videos']['total'])

    def get_search_results(self, search, search_response):
        if 'videos' not in search_response:
            return []
        # Vimeo only includes the 'video' key if there are actually videos on
        # the page.
        if int(search_response['videos']['on_this_page']) > 0:
            return search_response['videos']['video']
        return []

    def parse_search_result(self, search, result):
        # TODO: results have an embed_privacy key. What is this? Should
        # vidscraper return that information? Doesn't youtube have something
        # similar?
        video_id = result['id']
        if not result['upload_date']:
            # deleted video
            link = [u['_content'] for u in result['urls']['url']
                    if u['type'] == 'video'][0]
            raise VideoDeleted(link)
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
