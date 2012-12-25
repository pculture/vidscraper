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
import json
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

from vidscraper.exceptions import UnhandledVideo, UnhandledFeed
from vidscraper.suites import BaseSuite, registry
from vidscraper.utils.feedparser import struct_time_to_datetime
from vidscraper.videos import (BaseFeed, BaseSearch, VideoLoader,
                               OEmbedLoaderMixin, VideoFile)


# Information on the YouTube API can be found at the following links:
# * https://developers.google.com/youtube/2.0/developers_guide_protocol
# * https://developers.google.com/youtube/2.0/reference


class PathMixin(object):
    short_path_re = re.compile(r"^/(?P<video_id>[\w-]+)/?$")

    def get_url_data(self, url):
        parsed = urlparse.urlsplit(url)
        if parsed.scheme in ('http', 'https'):
            if (parsed.netloc in ('www.youtube.com', 'youtube.com') and
                parsed.path in ('/watch', '/watch/')):
                qsd = urlparse.parse_qs(parsed.query)
                try:
                    return {
                        'video_id': qsd['v'][0]
                    }
                except (KeyError, IndexError):
                    pass
            elif parsed.netloc == 'youtu.be':
                match = self.short_path_re.match(parsed.path)
                if match:
                    return match.groupdict()
        raise UnhandledVideo(url)


class ApiMixin(object):
    def get_headers(self):
        headers = super(ApiMixin, self).get_headers()
        if 'youtube_key' in self.api_keys:
            headers['X-GData-Key'] = "key=" + self.api_keys['youtube_key']
        return headers

    def get_video_data(self, item):
        username = item['author'][0]['uri']['$t'].rsplit('/', 1)[-1]
        if 'published' in item:
            date_key = 'published'
        else:
            date_key = 'updated'

        media_group = item['media$group']
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
        if '$t' in media_group['media$keywords']:
            tags = media_group['media$keywords']['$t'].split(', ')
        else:
            tags = []
        tags.extend(
            [cat['$t'] for cat in media_group['media$category']])
        data = {
            'link': item['link'][0]['href'].split('&', 1)[0],
            'title': item['title']['$t'],
            'description': description.replace('\r', ''),
            'thumbnail_url': thumbnail_url,
            'publish_datetime': datetime.strptime(item[date_key]['$t'],
                                                  "%Y-%m-%dT%H:%M:%S.000Z"),
            'tags': tags,
            'user': username,
            'user_url': u'http://www.youtube.com/user/{0}'.format(username),
            'guid' : 'http://gdata.youtube.com/feeds/api/videos/{0}'.format(
                        item['id']['$t'].split(':')[-1]),
            'license': media_group['media$license']['href'],
            'flash_enclosure_url': media_group['media$player']['url']
        }
        return data


class ApiLoader(ApiMixin, PathMixin, VideoLoader):
    fields = set(('link', 'title', 'description', 'guid', 'thumbnail_url',
                  'publish_datetime', 'tags', 'flash_enclosure_url', 'user',
                  'user_url', 'license'))

    url_format = u"http://gdata.youtube.com/feeds/api/videos/{video_id}?v=2&alt=json"

    def get_video_data(self, response):
        if response.status_code in (401, 403):
            return {'is_embeddable': False}
        parsed = json.loads(response.text)
        entry = parsed['entry']
        return ApiMixin.get_video_data(self, entry)


class VideoInfoLoader(PathMixin, VideoLoader):
    fields = set(('title', 'thumbnail_url', 'tags', 'files'))

    # the ordering of format codes we prefer to download
    # (code, mimetype, width, height)
    formats = (
        ('38', u'video/mp4', 4096, 3072),
        ('37', u'video/mp4', 1920, 1080),
        ('22', u'video/mp4', 1280, 720),
        ('18', u'video/mp4', 640, 360),
        ('35', u'video/x-flv', 854, 480),
        ('34', u'video/x-flv', 640, 360),
        ('6', u'video/x-flv', 480, 270),
        ('5', u'video/x-flv', 400, 240),
        ('45', u'video/webm', 1280, 720),
        ('44', u'video/webm', 854, 480),
        ('43', u'video/webm', 640, 360),
        ('84', u'video/mp4-3d', 1280, 720),
        ('85', u'video/mp4-3d', 1920, 520),
        ('82', u'video/mp4-3d', 640, 360),
        ('83', u'video/mp4-3d', 854, 240),
        ('102', u'video/webm-3d', 1280, 720),
        ('46', u'video/webm-3d', 1920, 540),
        ('101', u'video/webm-3d', 854, 480),
        ('100', u'video/webm-3d', 640, 360),
    )

    url_format = u"http://www.youtube.com/get_video_info?video_id={video_id}&el=embedded&ps=default&eurl="

    def get_video_data(self, response):
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
            'thumbnail_url': params['thumbnail_url'][0],
            }
        if 'keywords' in params:
            data['tags'] = params['keywords'][0].decode('utf8').split(',')
        if data['thumbnail_url'].endswith('/default.jpg'):
            # got a crummy version; increase the resolution
            data['thumbnail_url'] = data['thumbnail_url'].replace(
                '/default.jpg', '/hqdefault.jpg')

        url_querystrings = params["url_encoded_fmt_stream_map"][0].split(",")
        url_data = [urlparse.parse_qs(qs) for qs in url_querystrings]
        url_data_map = dict((ud['itag'][0], ud) for ud in url_data if 'itag' in ud)

        data['files'] = []
        for code, mime_type, width, height in self.formats:
            if code in url_data_map:
                file_data = url_data_map[code]
                parsed_file_url = urlparse.urlsplit(file_data['url'][0])
                parsed_file_url_qs = dict(urlparse.parse_qsl(parsed_file_url.query))
                expires = struct_time_to_datetime(time.gmtime(int(parsed_file_url_qs['expire'])))
                parsed_file_url_qs['signature'] = file_data['sig'][0]
                url = urlparse.urlunsplit(parsed_file_url[:3] +
                                          (urllib.urlencode(parsed_file_url_qs),) +
                                          parsed_file_url[4:])
                data['files'].append(VideoFile(url=url,
                                               expires=expires,
                                               mime_type=mime_type,
                                               width=width,
                                               height=height))
        return data


class OEmbedLoader(OEmbedLoaderMixin, PathMixin, VideoLoader):
    endpoint = u"http://www.youtube.com/oembed"
    url_format = u"http://www.youtube.com/watch?v={video_id}"

    def get_video_data(self, response):
        if response.status_code in (requests.codes.unauthorized,
                                    requests.codes.forbidden):
            return {'is_embeddable': False}
        if response.status_code == 404:
            return {}
        return super(OEmbedLoader, self).get_video_data(response)


class Feed(ApiMixin, BaseFeed):
    per_page = 50
    page_url_format = ('http://gdata.youtube.com/feeds/api/users/{username}/'
                       'uploads?alt=json&v=2&start-index={page_start}&max-results={page_max}')
    path_re = re.compile(r'^/(?:user/)?(?P<username>\w+)(?:/videos)?/?$')
    # old_path_re means that the username is in the GET params as 'user'
    old_path_re = re.compile(r'^/profile(?:_videos)?/?$')
    gdata_re = re.compile(r'^/feeds/(?:base|api)/users/(?P<username>\w+)/?')

    #: Usernames can be at youtube.com/<username> - these are words which
    #: therefore can't be used as usernames, since they already have meanings
    #: at the root. This isn't a comprehensive list, just the ones people will
    #: probably interact the most with.
    invalid_usernames = set(('user', 'profile', 'profile_videos', 'watch',
                             'playlist', 'embed'))

    def get_url_data(self, url):
        parsed_url = urlparse.urlsplit(url)
        if parsed_url.scheme in ('http', 'https'):
            if parsed_url.netloc in ('youtube.com', 'www.youtube.com'):
                match = self.path_re.match(parsed_url.path)
                if (match and
                    match.group('username') not in self.invalid_usernames):
                    return match.groupdict()

                match = self.old_path_re.match(parsed_url.path)
                if match:
                    parsed_qs = urlparse.parse_qs(parsed_url.query)
                    if 'user' in parsed_qs:
                        username = parsed_qs['user'][0]
                        if username not in self.invalid_usernames:
                            return {'username': username}
            elif parsed_url.netloc == 'gdata.youtube.com':
                match = self.gdata_re.match(parsed_url.path)
                if match:
                    return match.groupdict()

        raise UnhandledFeed(url)

    def get_response_items(self, response):
        return response.json['feed'].get('entry', [])

    def data_from_response(self, response):
        feed = response.json['feed']
        for l in feed['link']:
            if l['rel'] == 'alternate':
                link = l['href']
                break
        else:
            link = None
        return {
            'video_count': feed['openSearch$totalResults']['$t'],
            'title': feed['title']['$t'],
            'webpage': link,
            'guid': feed['id']['$t'],
            'etag': response.headers['etag'] or feed['gd$etag'],
            'thumbnail_url': feed['logo']['$t'],
        }


class Search(ApiMixin, BaseSearch):
    per_page = 50
    page_url_format = ('http://gdata.youtube.com/feeds/api/videos?v=2&alt=json&'
                       'q={query}&orderby={order_by}&start-index={page_start}&'
                       'max-results={page_max}')

    # YouTube's search supports relevance, published, viewCount, and rating.
    order_by_map = {
        'relevant': 'relevance',
        'latest': 'published',
        'popular': 'viewCount',
    }

    def get_response_items(self, response):
        # Response will have a 400 error code if we're beyond the end of the
        # search results (max 999).
        if response.status_code == 400:
            return []
        return response.json['feed'].get('entry', [])

    def data_from_response(self, response):
        # Response will have a 400 error code (and no useful metadata) if
        # we're beyond the end of the search results (max 999).
        if response.status_code == 400:
            return {}
        feed = response.json['feed']
        return {
            'video_count': feed['openSearch$totalResults']['$t'],
        }


class Suite(BaseSuite):
    loader_classes = (OEmbedLoader, ApiLoader,
                      VideoInfoLoader)

    feed_class = Feed
    search_class = Search


registry.register(Suite)
