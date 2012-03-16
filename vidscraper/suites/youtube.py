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

import re
import time
import urllib
import urlparse

from BeautifulSoup import BeautifulSoup

import feedparser
# add the OpenSearch namespace to FeedParser
# http://code.google.com/p/feedparser/issues/detail?id=55
feedparser._FeedParserMixin.namespaces[
    'http://a9.com/-/spec/opensearch/1.1/'] = 'opensearch'

from vidscraper.suites import BaseSuite, registry
from vidscraper.utils.feedparser import get_entry_thumbnail_url
from vidscraper.utils.feedparser import struct_time_to_datetime

class YouTubeSuite(BaseSuite):
    video_regex = r'^https?://(' +\
    r'([^/]+\.)?youtube.com/(?:watch)?\?(\w+=[^&]+&)*v=' +\
                  r'|youtu.be/)(?P<video_id>[\w-]+)'
    feed_regex = r'^https?://([^/]+\.)?youtube.com/'
    feed_regexes = [re.compile(r) for r in (
            (r'^(http://)?(www\.)?youtube\.com/profile(_videos)?'
             r'\?(\w+=\w+&)*user=(?P<name>\w+)'),
            (r'^(http://)?(www\.)?youtube\.com/((rss/)?user/)?'
             r'(?P<name>\w+)'),
            (r'^(https?://)?gdata.youtube.com/feeds/base/users/(?P<name>\w+)'
             ))]
    feed_url_base = ('http://gdata.youtube.com/feeds/base/users/%s/'
                    'uploads?alt=rss&v=2')

    oembed_endpoint = "http://www.youtube.com/oembed"
    api_fields = set(['link', 'title', 'description', 'guid',
                      'thumbnail_url', 'publish_datetime', 'tags',
                      'flash_enclosure_url', 'user', 'user_url', 'license'])

    scrape_fields = set(['title', 'thumbnail_url', 'user', 'user_url', 'tags',
                         'file_url', 'file_url_mimetype', 'file_url_expires'])

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

    def get_feed_url(self, url, extra_params=None):
        for regex in self.feed_regexes:
            match = regex.match(url)
            if match:
                name = match.group('name')
                url = self.feed_url_base % name
                break
        if extra_params:
            url = '%s&%s' % (url, urllib.urlencode(extra_params))
        return url

    def parse_error(self, exc):
        code = getattr(exc, 'code', None)
        if code in (401, 403): # Unauthorized, Forbidden
            return {'is_embeddable': False}
        elif code == 404: # Not found
            return {}
        else:
            raise exc

    parse_oembed_error = parse_api_error = parse_error

    def parse_feed_entry(self, entry):
        """
        Reusable method to parse a feedparser entry from a youtube rss feed.
        Returns a dictionary mapping :class:`.Video` fields to values.

        """
        user = entry['author']
        if 'published_parsed' in entry:
            best_date = struct_time_to_datetime(entry['published_parsed'])
        else:
            best_date = struct_time_to_datetime(entry['updated_parsed'])
        if ('summary_detail' in entry and
            entry['summary_detail']['type'] == 'text/html'):
            # HTML-ified description in RSS feeds
            soup = BeautifulSoup(entry['summary']).findAll('span')[0]
            description = unicode(soup.string)
        else:
            description = entry['summary']
        data = {
            'link': entry['links'][0]['href'].split('&', 1)[0],
            'title': entry['title'],
            'description': description,
            'thumbnail_url': get_entry_thumbnail_url(entry),
            'publish_datetime': best_date,
            'tags': [t['term'] for t in entry['tags']
                    if not t['term'].startswith('http')],
            'user': user,
            'user_url': u'http://www.youtube.com/user/%s' % user,
            'guid' : entry['id'],
        }
        if entry.id.startswith('tag:youtube.com'):
            data['guid'] = 'http://gdata.youtube.com/feeds/api/videos/%s' % (
                entry.id.split(':')[-1],)
        if 'media_player' in entry: # only in search feeds/API?
            data['flash_enclosure_url'] = entry['media_player']['url']
        if data['thumbnail_url'].endswith('/default.jpg'):
            # got a crummy version; increase the resolution
            data['thumbnail_url'] = data['thumbnail_url'].replace(
                '/default.jpg', '/hqdefault.jpg')
        return data

    def get_feed_entry_count(self, feed, feed_response):
        return int(feed_response.feed.get('opensearch_totalresults',
                                          len(feed_response.entries)))

    def get_api_url(self, video):
        video_id = self.video_regex.match(video.url).group('video_id')
        return "http://gdata.youtube.com/feeds/api/videos/%s?v=2" % video_id

    def parse_api_response(self, response_text):
        parsed = feedparser.parse(response_text)
        entry = parsed.entries[0]
        user = entry['author']
        best_date = struct_time_to_datetime(entry['published_parsed'])
        data = {
            'link': entry['links'][0]['href'].split('&', 1)[0],
            'title': entry['title'],
            'description': entry['media_group'],
            'thumbnail_url': get_entry_thumbnail_url(entry),
            'publish_datetime': best_date,
            'tags': [t['term'] for t in entry['tags']
                    if not t['term'].startswith('http')],
            'user': user,
            'user_url': u'http://www.youtube.com/user/%s' % user,
            'guid' : 'http://gdata.youtube.com/feeds/api/videos/%s' % (
                entry.id.split(':')[-1],),
            'license': entry['media_license']['href'],
            'flash_enclosure_url': entry['media_player']['url']
        }
        if data['thumbnail_url'].endswith('/default.jpg'):
            # got a crummy version; increase the resolution
            data['thumbnail_url'] = data['thumbnail_url'].replace(
                '/default.jpg', '/hqdefault.jpg')
        if (data['description'][:len(data['user'])].lower().startswith(
                data['user'].lower()) and
            data['description'].endswith('youtube')):
            # description looks like "USERNAME[real description]youtube"
            data['description'] = data['description'][len(data['user']):-7]
        return data

    def get_scrape_url(self, video):
        video_id = self.video_regex.match(video.url).group('video_id')
        return (u"http://www.youtube.com/get_video_info?video_id=%s&"
                "el=embedded&ps=default&eurl=" % video_id)

    def parse_scrape_response(self, response_text):
        params = urlparse.parse_qs(response_text)
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

    def parse_scrape_error(self, exc):
        if getattr(exc, 'code', None) == 402:
            # can happen when we make too many requests
            # XXX re-raise, or just ignore?
            return {}
        raise exc

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

    def get_next_feed_page_url(self, feed, feed_response):
        extra_params = self.get_next_page_url_params(feed_response)
        if not extra_params:
            return None
        return self.get_feed_url(feed.url, extra_params=extra_params)

registry.register(YouTubeSuite)
