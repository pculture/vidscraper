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
import time
import urllib
import urlparse

from bs4 import BeautifulSoup

import feedparser
# add the OpenSearch namespace to FeedParser
# http://code.google.com/p/feedparser/issues/detail?id=55
feedparser._FeedParserMixin.namespaces[
    'http://a9.com/-/spec/opensearch/1.1/'] = 'opensearch'
import requests

from vidscraper.exceptions import UnhandledURL
from vidscraper.suites import BaseSuite, registry, SuiteMethod, OEmbedMethod
from vidscraper.utils.feedparser import get_entry_thumbnail_url
from vidscraper.utils.feedparser import struct_time_to_datetime
from vidscraper.videos import VideoFeed


class YouTubeApiMethod(SuiteMethod):
    fields = set(('link', 'title', 'description', 'guid', 'thumbnail_url',
                  'publish_datetime', 'tags', 'flash_enclosure_url', 'user',
                  'user_url', 'license'))

    def get_url(self, video):
        video_id = video.suite.video_regex.match(video.url).group('video_id')
        return "http://gdata.youtube.com/feeds/api/videos/{0}?v=2&alt=json".format(video_id)

    def process(self, response):
        if response.status_code in (401, 403):
            return {'is_embeddable': False}
        parsed = json.loads(response.text)
        entry = parsed['entry']
        return YouTubeSuite.parse_api_video(entry)


class YouTubeScrapeMethod(SuiteMethod):
    fields = set(('title', 'thumbnail_url', 'user', 'user_url', 'tags',
                  'file_url', 'file_url_mimetype', 'file_url_expires'))

    # the ordering of fmt codes we prefer to download
    preferred_fmt_types = [
        (38, u'video/mp4'), # 4096x3072
        (37, u'video/mp4'), # 1920x1080
        (22, u'video/mp4'), # 1280x720
        (18, u'video/mp4'), # 640x360
        (35, u'video/x-flv'), # 854x480, MPEG-4 encoded
        (34, u'video/x-flv'), # 640x360, MPEG-4 encoded
        (6, u'video/x-flv'), # 480x270
        (5, u'video/x-flv'), # 400x240
        ]

    def get_url(self, video):
        video_id = video.suite.video_regex.match(video.url).group('video_id')
        return (u"http://www.youtube.com/get_video_info?video_id=%s&"
                "el=embedded&ps=default&eurl=" % video_id)

    def process(self, response):
        if response.status_code == 402:
            # 402: Payment required.
            # A note in the previous code said this could happen when too many
            # requests were made (per second?) Unclear why, though, or why
            # this is only caught here.
            return {}
        params = urlparse.parse_qs(response.text.encode('utf-8'))
        if params['status'][0] == 'fail':
            if params['errorcode'][0] == '150': # unembedable
                return {'is_embeddable': False}
            return {}
        data = {
            'title': params['title'][0].decode('utf8'),
            'user': params['author'][0].decode('utf8'),
            'user_url': u'http://www.youtube.com/user/%s' % (
                params['author'][0].decode('utf8')),
            'thumbnail_url': params['thumbnail_url'][0],
            }
        if 'keywords' in params:
            data['tags'] = params['keywords'][0].decode('utf8').split(',')
        if data['thumbnail_url'].endswith('/default.jpg'):
            # got a crummy version; increase the resolution
            data['thumbnail_url'] = data['thumbnail_url'].replace(
                '/default.jpg', '/hqdefault.jpg')

        # fmt_url_map is a comma separated list of pipe separated
        # pairs of fmt, url
        # build the format codes.
        fmt_list = [int(x.split('/')[0])
                    for x in params['fmt_list'][0].split(',')]
        # build the list of available urls.
        fmt_url_map = params["url_encoded_fmt_stream_map"][0].split(",")
        # strip url= from url=xxxxxx, strip trailer.
        fmt_url_map = [urllib.unquote_plus(x[4:]).split(';')[0]
                       for x in fmt_url_map]
        # now build the actual fmt_url_map ...
        fmt_url_map = dict(zip(fmt_list, fmt_url_map))
        for fmt, mimetype in self.preferred_fmt_types:
            if fmt in fmt_url_map:
                data['file_url'] = file_url = fmt_url_map[fmt]
                data['file_url_mimetype'] = mimetype
                parsed_url = urlparse.urlparse(file_url)
                file_url_qs = urlparse.parse_qs(parsed_url.query)
                data['file_url_expires'] = struct_time_to_datetime(
                    time.gmtime(int(file_url_qs['expire'][0])))
        return data


class YouTubeOEmbedMethod(OEmbedMethod):
    def process(self, response):
        if response.status_code in (requests.codes.unauthorized,
                                    requests.codes.forbidden):
            return {'is_embeddable': False}
        if response.status_code == 404:
            return {}
        return OEmbedMethod.process(self, response)


class YouTubeFeed(VideoFeed):
    per_page = 50
    page_url_format = ('http://gdata.youtube.com/feeds/api/users/{username}/'
                       'uploads?alt=rss&v=2&start-index={page_start}&max-results={page_max}')
    path_re = re.compile(r'^/(?:user/)?(?P<username>\w+)/?$')
    # old_path_re means that the username is in the GET params as 'user'
    old_path_re = re.compile(r'^/profile(?:_videos)/?$')
    gdata_re = re.compile(r'^/feeds/(?:base|api)/users/(?P<username>\w+)/?')

    def get_url_data(self, url):
        parsed_url = urlparse.urlsplit(url)
        if parsed_url.scheme not in ('http', 'https'):
            raise UnhandledURL

        if parsed_url.netloc in ('youtube.com', 'www.youtube.com'):
            match = self.path_re.match(parsed_url.path)
            if match:
                return match.groupdict()
            
            match = self.old_path_re.match(parsed_url.path)
            if match:
                parsed_qs = urlparse.parse_qs(parsed_url.query)
                if 'user' not in parsed_qs:
                    raise UnhandledURL
                return {'username': parsed_qs['user'][0]}
        elif parsed_url.netloc == 'gdata.youtube.com':
            match = self.gdata_re.match(parsed_url.path)
            if match:
                return match.groupdict()

        raise UnhandledURL

    def get_item_data(self, item):
        return YouTubeSuite.parse_api_video(item)

    def get_page(self, page_start, page_max):
        url = self.get_page_url(page_start, page_max)
        response = requests.get(url)
        response._parsed = json.loads(response.text)
        return response

    def data_from_response(self, response):
        feed = response._parsed['feed']
        return {
            'video_count': feed['openSearch$totalResults']['$t'],
            'title': feed['title']['$t'],
            'webpage': feed['link'],
            'guid': feed['id']['$t'],
            'etag': response.headers['etag']
        }

    def get_response_items(self, response):
        return response._parsed['feed']['entry']


class YouTubeSuite(BaseSuite):
    video_regex = r'^https?://(' +\
    r'([^/]+\.)?youtube.com/(?:watch)?\?(\w+=[^&]+&)*v=' +\
                  r'|youtu.be/)(?P<video_id>[\w-]+)'

    methods = (YouTubeOEmbedMethod("http://www.youtube.com/oembed"),
               YouTubeApiMethod(), YouTubeScrapeMethod())

    feed_class = YouTubeFeed

    @staticmethod
    def parse_api_video(video):
        username = video['author'][0]['name']['$t']
        if 'published' in video:
            date_key = 'published'
        else:
            date_key = 'updated'

        media_group = video['media$group']
        description = media_group['media$description']
        if description['type'] != 'plain':
            # HTML-ified description. SB: Is this correct? Added in
            # 5ca9e928 originally.
            soup = BeautifulSoup(description['$t']).findAll('span')[0]
            description = unicode(soup.string)
        else:
            description = description['$t']

        thumbnail_url = None
        for thumbnail in media_group['media$thumbnail']:
            if thumbnail_url is None and thumbnail['yt$name'] == 'default':
                thumbnail_url = thumbnail['url']
            if thumbnail['yt$name'] == 'hqdefault':
                thumbnail_url = thumbnail['url']
                break
        data = {
            'link': video['link'][0]['href'].split('&', 1)[0],
            'title': video['title']['$t'],
            'description': description,
            'thumbnail_url': thumbnail_url,
            'publish_datetime': datetime.strptime(video[date_key]['$t'],
                                                  "%Y-%m-%dT%H:%M:%S.000Z"),
            'tags': media_group['media$keywords']['$t'].split(', '),
            'user': username,
            'user_url': u'http://www.youtube.com/user/{0}'.format(username),
            'guid' : 'http://gdata.youtube.com/feeds/api/videos/{0}'.format(
                        video['id'].split(':')[-1]),
            'license': media_group['media$license']['href'],
            'flash_enclosure_url': media_group['media$player']['url']
        }
        return data

    def get_search_url(self, search, extra_params=None):
        params = {
            'vq': search.query,
        }
        if extra_params is not None:
            params.update(extra_params)
        if search.order_by == 'relevant':
            params['orderby'] = 'relevance'
        elif search.order_by == 'latest':
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

    def get_next_search_page_url(self, search, search_response):
        extra_params = self.get_next_page_url_params(search_response)
        if not extra_params:
            return None
        return self.get_search_url(
            search,
            extra_params=extra_params)

registry.register(YouTubeSuite)
