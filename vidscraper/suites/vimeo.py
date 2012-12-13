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
import re
import urlparse
import warnings

try:
    import oauth_hook
except ImportError:
    oauth_hook = None
import requests

from vidscraper.exceptions import (VideoDeleted, UnhandledVideo,
                                   UnhandledFeed, UnhandledSearch)
from vidscraper.suites import BaseSuite, registry
from vidscraper.videos import (BaseFeed, BaseSearch, VideoLoader,
                               OEmbedLoaderMixin)


# Documentation for the Vimeo APIs:
# * http://vimeo.com/api


class PathMixin(object):
    url_re = re.compile(r'https?://(?:[^/]+\.)?vimeo.com/(?P<video_id>\d+)')

    def get_url_data(self, url):
        match = self.url_re.match(url)
        if match:
            return match.groupdict()

        raise UnhandledVideo(url)


class AdvancedApiMixin(object):
    """
    Provides some common functionality for the vimeo advanced API.

    """
    def is_available(self):
        return ('vimeo_key' in self.api_keys and
                'vimeo_secret' in self.api_keys and
                oauth_hook is not None)

    def get_request_kwargs(self):
        hook = oauth_hook.OAuthHook(consumer_key=self.api_keys['vimeo_key'],
                                consumer_secret=self.api_keys['vimeo_secret'],
                                header_auth=True)
        kwargs = super(AdvancedApiMixin, self).get_request_kwargs()
        kwargs['hooks'] = {'pre_request': hook}
        return kwargs

    def get_video_data(self, item):
        # TODO: items have an embed_privacy key. What is this? Should
        # vidscraper return that information? Doesn't youtube have something
        # similar?
        if not item['upload_date']:
            # deleted video
            link = [u['_content'] for u in item['urls']['url']
                    if u['type'] == 'video'][0]
            raise VideoDeleted(link)
        data = {
            'title': item['title'],
            'link': [u['_content'] for u in item['urls']['url']
                    if u['type'] == 'video'][0],
            'description': item['description'],
            'thumbnail_url': item['thumbnails']['thumbnail'][2]['_content'],
            'user': item['owner']['realname'],
            'user_url': item['owner']['profileurl'],
            'publish_datetime': datetime.datetime.strptime(
                    item['upload_date'], '%Y-%m-%d %H:%M:%S'),
            'tags': [t['_content']
                            for t in item.get('tags', {}).get('tag', [])],
            'flash_enclosure_url': Suite.video_flash_enclosure(item['id']),
            'guid': Suite.video_guid(item['upload_date'], item['id']),
        }
        return data


class OEmbedLoader(PathMixin, OEmbedLoaderMixin, VideoLoader):
    endpoint = u"http://vimeo.com/api/oembed.json"
    url_format = u"http://vimeo.com/{video_id}"


class SimpleLoader(PathMixin, VideoLoader):
    fields = set(['link', 'title', 'description', 'tags', 'guid',
                  'publish_datetime', 'thumbnail_url', 'user', 'user_url',
                  'flash_enclosure_url'])

    url_format = u"http://vimeo.com/api/v2/video/{video_id}.json"

    def get_video_data(self, response):
        return Suite.simple_api_video_to_data(response.json[0])


class AdvancedLoader(AdvancedApiMixin, PathMixin, VideoLoader):
    fields = set(['title', 'link', 'description', 'thumbnail_url', 'user',
                  'user_url', 'publish_datetime', 'tags', 'guid',
                  'flash_enclosure_url'])
    url_format = (u"http://vimeo.com/api/rest/v2?format=json&full_response=1&"
                  u"method=vimeo.videos.getInfo&video_id={video_id}")

    def get_url_data(self, url):
        if not self.is_available():
            raise UnhandledVideo(url)
        return super(AdvancedLoader, self).get_url_data(url)

    def get_video_data(self, response):
        return AdvancedApiMixin.get_video_data(self,
                                               response.json['video'][0])


class SimpleFeed(BaseFeed):
    """
    Vimeo supports the following feeds for videos through its "Simple API":

    * http://vimeo.com/api/v2/album/<album_id>/videos.json
    * http://vimeo.com/api/v2/channel/<channelname>/videos.json
    * http://vimeo.com/api/v2/group/<groupname>/videos.json

    as well as the following "user video" feeds:

    http://vimeo.com/api/v2/<username>/videos.json
        Videos created by the user

    http://vimeo.com/api/v2/<username>/likes.json
        Videos the user likes

    http://vimeo.com/api/v2/<username>/appears_in.json
        Videos that the user appears in

    http://vimeo.com/api/v2/<username>/all_videos.json
        Videos that the user appears in and created

    http://vimeo.com/api/v2/<username>/subscriptions.json
        Videos the user is subscribed to

    The simple API only provides up to 60 videos in each feed, but can be used
    without authentication.

    """
    path_re = re.compile(r'(?:^/album/(?P<album_id>\d+)(?:/format:\w+)?/?)$|'
                         r'(?:^/channels/(?P<channel_id>\w+)(?:/videos/rss)?/?)$|'
                         r'(?:^/groups/(?P<group_id>\w+)(?:/videos(?:/sort:\w+(?:/format:\w+)?)?)?/?)$|'
                         r'(?:^/(?P<user_id>\w+)(?:/(?P<request_type>videos|likes)(?:/sort:\w+(?:/format:\w+)?|/rss)?)?/?)$')

    api_re = re.compile(r'(?:^/api/v2/(?:album/(?P<album_id>\d+)|channel/(?P<channel_id>\w+)|group/(?P<group_id>\w+)|(?P<user_id>\w+))/(?P<request_type>\w+)\.(?:json|php|xml))')

    page_url_format = u"http://vimeo.com/api/v2/{api_path}/{request_type}.json?page={page}"
    info_url_format = u"http://vimeo.com/api/v2/{api_path}/info.json"
    per_page = 20

    def __init__(self, *args, **kwargs):
        super(SimpleFeed, self).__init__(*args, **kwargs)
        warnings.warn("The simple API can only retrieve up to 60 results "
                      "from a feed.")

    def get_url_data(self, url):
        parsed_url = urlparse.urlsplit(url)
        if parsed_url.scheme in ('http', 'https'):
            if parsed_url.netloc in ('vimeo.com', 'www.vimeo.com'):
                match = self.path_re.match(parsed_url.path)
                if not match:
                    # Only use the api regex as a fallback - less likely to
                    # see it.
                    match = self.api_re.match(parsed_url.path)

                if match:
                    return match.groupdict()
        raise UnhandledFeed(url)

    def get_api_path(self, data):
        if data['user_id']:
            return data['user_id']
        else:
            if data['album_id']:
                return "album/{0}".format(data['album_id'])
            elif data['channel_id']:
                return "channel/{0}".format(data['channel_id'])
            elif data['group_id']:
                return "group/{0}".format(data['group_id'])

        raise ValueError(u"No path buildable with given data.")

    def get_page_url_data(self, *args, **kwargs):
        data = super(SimpleFeed, self).get_page_url_data(*args, **kwargs)
        if (data['user_id'] and
            data['request_type'] in ('videos', 'likes', 'appears_in',
                                     'all_videos', 'subscriptions')):
            request_type = data['request_type']
        else:
            request_type = 'videos'
        data.update({
            'api_path': self.get_api_path(data),
            'request_type': request_type
        })
        return data

    def get_response_items(self, response):
        if response.status_code == 403:
            return []
        return response.json

    def get_video_data(self, item):
        return Suite.simple_api_video_to_data(item)

    def load(self):
        """
        Vimeo returns data about feeds from a different part of the API, so we
        handle loading differently than for default feeds.

        """
        if not self._loaded:
            url = self.info_url_format.format(
                                    api_path=self.get_api_path(self.url_data))
            response = requests.get(url)
            data = self.data_from_response(response)

            if self._response is None:
                self._next_page()

            data['etag'] = self._response.headers['etag']

            self._apply(data)
            self._loaded = True

    def data_from_response(self, response):
        """
        The response here is expected to be an *info* response for the feed,
        which always uses the simple api, since there is no api for album
        info.

        """
        data = {}
        # User is very different
        if "display_name" in response.json:
            display_name = response.json['display_name']
            request_type = (self.url_data['request_type'] if
                            self.url_data['request_type'] in
                            ('videos', 'likes', 'appears_in',
                             'all_videos', 'subscriptions')
                            else 'videos')
            count = None
            webpage = response.json['profile_url']
            if request_type == 'videos':
                title = "{0}'s videos".format(display_name)
                count = response.json['total_videos_uploaded']
                webpage = response.json['videos_url']
            elif request_type == 'likes':
                title = 'Videos {0} likes'.format(display_name)
                count = response.json['total_videos_liked']
                webpage = "{0}/likes".format(webpage)
            elif request_type == 'appears_in':
                title = "Videos {0} appears in".format(display_name)
                count = response.json['total_videos_appears_in']
            elif request_type == 'all_videos':
                title = "{0}'s videos and videos {0} appears in".format(
                            display_name)
            elif request_type == 'subscriptions':
                title = "Videos {0} is subscribed to".format(display_name)
            data.update({
                'title': title,
                # if this is the simple API, we can only get up to 60 videos;
                # if it's the advanced API, this will be overridden anyway.
                'video_count': min(count, 60),
                'description': response.json['bio'],
                'webpage': webpage,
                'thumbnail_url': response.json['portrait_huge']
            })
        else:
            # It's a channel, album, or group feed.

            # Title - albums use 'title'; channels/groups use 'name'
            if "title" in response.json:
                title = response.json['title']
            else:
                title = response.json['name']

            # Albums and groups have a small thumbnail (~100x75). Groups and
            # channels have a large logo, as well, but it seems like a paid
            # feature - some groups/channels have a blank value there.
            thumbnail_url = response.json.get('logo')
            if not thumbnail_url and 'thumbnail' in response.json:
                thumbnail_url = response.json['thumbnail']

            data.update({
                'title': title,
                # if this is the simple API, we can only get up to 60 videos;
                # if it's the advanced API, this will be overridden anyway.
                'video_count': min(response.json['total_videos'], 60),
                'description': response.json['description'],
                'webpage': response.json['url'],
                'thumbnail_url': thumbnail_url
            })

        return data


class AdvancedIteratorMixin(AdvancedApiMixin):
    """
    Mixin class to be used with VideoIterators to provide standard access to
    Vimeo's advanced API.

    """
    page_url_format = (u"http://vimeo.com/api/rest/v2?format=json&full_response=1&per_page=50&"
                       u"method=vimeo.{method}&sort={sort}&page={page}&{method_params}")
    per_page = 50

    def get_page(self, page_start, page_max):
        url = self.get_page_url(page_start, page_max)
        return self.request(url)

    def data_from_response(self, response):
        # Advanced api doesn't have etags, but it does have explicit
        # video counts.
        if 'videos' not in response.json:
            video_count = 0
        else:
            video_count = int(response.json['videos']['total'])
        return {'video_count': video_count}

    def get_response_items(self, response):
        if 'videos' not in response.json:
            return []

        # A blank page will not include the 'video' key.
        if response.json['videos']['on_this_page'] == 0:
            return []

        return response.json['videos']['video']


class Search(AdvancedIteratorMixin, BaseSearch):
    # Vimeo's search api supports relevant, newest, oldest, most_played,
    # most_commented, and most_liked.
    order_by_map = {
        'relevant': 'relevant',
        'latest': 'newest',
        '-latest': 'oldest',
        'popular': 'most_played'
    }

    def __init__(self, query, order_by='relevant', **kwargs):
        super(Search, self).__init__(query, order_by, **kwargs)
        if not self.is_available():
            if oauth_hook is None:
                raise UnhandledSearch(u"{0} requires requests-oauth.".format(
                                      self.__class__.__name__))
            else:
                raise UnhandledSearch(u"{0} requires API keys.".format(
                                      self.__class__.__name__))

    def get_page_url_data(self, page_start, page_max):
        data = super(Search, self).get_page_url_data(page_start,
                                                          page_max)
        data.update({
            'method': 'videos.search',
            'method_params': 'query={0}'.format(data['query']),
            'sort': data['order_by'],
        })
        return data


class AdvancedFeed(AdvancedIteratorMixin, SimpleFeed):
    """
    Vimeo's advanced API which provides the following feeds through its
    "methods":

    * albums.getVideos
    * channels.getVideos
    * groups.getVideos
    * videos.getUploaded
    * videos.getLiked
    * videos.getAppearsIn
    * videos.getAll
    * videos.getSubscriptions

    """
    def __init__(self, *args, **kwargs):
        super(AdvancedFeed, self).__init__(*args, **kwargs)
        if not self.is_available():
            if oauth_hook is None:
                raise UnhandledFeed(u"{0} requires requests-oauth.".format(
                                    self.__class__.__name__))
            else:
                raise UnhandledFeed(u"{0} requires API keys.".format(
                                    self.__class__.__name__))

    def get_page_url_data(self, *args, **kwargs):
        data = super(AdvancedFeed, self).get_page_url_data(*args, **kwargs)
        if data['user_id']:
            method_params = "user_id={0}".format(data['user_id'])
            request_type = data['request_type']
            if request_type == 'likes':
                method = 'getLiked'
            elif request_type == 'appears_in':
                method = 'getAppearsIn'
            elif request_type == 'all_videos':
                method = 'getAll'
            elif request_type == 'subscriptions':
                method = 'getSubscriptions'
            else:
                # This covers 'videos' and any invalid or unknown methods.
                method = 'getUploaded'
            method = "videos.{0}".format(method)
        elif data['album_id']:
            method_params = "album_id={0}".format(data['album_id'])
            method = "albums.getVideos"
        elif data['channel_id']:
            method_params = "channel_id={0}".format(data['channel_id'])
            method = "channels.getVideos"
        elif data['group_id']:
            method_params = "group_id={0}".format(data['group_id'])
            method = "groups.getVideos"
        else:
            raise ValueError(u"Method can't be calculated with given "
                             u"data.")
        data.update({
            'method_params': method_params,
            'method': method,
            'sort': 'newest',
        })
        return data

    def load(self):
        if not self._loaded:
            url = self.info_url_format.format(
                                    api_path=self.get_api_path(self.url_data))
            response = requests.get(url)
            data = SimpleFeed.data_from_response(self, response)

            if self._response is None:
                self._next_page()

            data.update(
                AdvancedIteratorMixin.data_from_response(self,
                                                              self._response))
            self._apply(data)
            self._loaded = True


class Suite(BaseSuite):
    """
    Suite for vimeo.com. Currently supports their oembed api and simple api. No
    API key is required for this level of access.

    """
    loader_classes = (OEmbedLoader, AdvancedLoader, SimpleLoader)
    search_class = Search

    def get_feed(self, url, *args, **kwargs):
        try:
            return AdvancedFeed(url, *args, **kwargs)
        except UnhandledFeed:
            return SimpleFeed(url, *args, **kwargs)

    @staticmethod
    def video_flash_enclosure(video_id):
        return u'http://vimeo.com/moogaloop.swf?clip_id={0}'.format(video_id)

    @staticmethod
    def video_guid(video_upload_date, video_id):
        return u'tag:vimeo,{0}:clip{1}'.format(video_upload_date[:10],
                                               video_id)

    @classmethod
    def simple_api_video_to_data(cls, api_video):
        """
        Takes a video dictionary from a vimeo API response and returns a
        dictionary mapping field names to values.

        """
        data = {
            'title': api_video['title'],
            'link': api_video['url'],
            'description': api_video['description'],
            'thumbnail_url': api_video['thumbnail_large'],
            'user': api_video['user_name'],
            'user_url': api_video['user_url'],
            'publish_datetime': datetime.datetime.strptime(
                api_video['upload_date'], '%Y-%m-%d %H:%M:%S'),
            'tags': [tag for tag in api_video['tags'].split(', ') if tag],
            'flash_enclosure_url': cls.video_flash_enclosure(api_video['id']),
            'guid': cls.video_guid(api_video['upload_date'], api_video['id'])
        }
        return data


registry.register(Suite)
