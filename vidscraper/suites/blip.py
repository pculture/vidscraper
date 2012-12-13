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
import urlparse

import feedparser

from vidscraper.exceptions import UnhandledVideo, UnhandledFeed, InvalidVideo
from vidscraper.suites import BaseSuite, registry
from vidscraper.utils.feedparser import (get_entry_thumbnail_url,
                                         get_accepted_enclosures)
from vidscraper.videos import (FeedparserFeed, FeedparserSearch,
                               VideoLoader, OEmbedLoaderMixin, VideoFile)


class PathMixin(object):
    new_path_re = re.compile(r'^/(?P<user>[\w-]+)/(?P<slug>[\w-]+)-(?P<post_id>\d+)/?$')
    old_path_re = re.compile(r'^/file/(?P<item_id>\d+)/?$', re.I)

    new_url_format = "http://blip.tv/rss/{post_id}"
    old_url_format = "http://blip.tv/file/{item_id}?skin=rss"

    def get_url_data(self, url):
        parsed_url = urlparse.urlsplit(url)
        if (parsed_url.scheme in ('http', 'https') and
            parsed_url.netloc in ('blip.tv', 'www.blip.tv')):
            match = self.new_path_re.match(parsed_url.path)
            if match:
                return match.groupdict()
            else:
                match = self.old_path_re.match(parsed_url.path)
                if match:
                    return match.groupdict()

        raise UnhandledVideo(url)

    def get_url(self):
        try:
            return self.new_url_format.format(**self.url_data)
        except KeyError:
            return self.old_url_format.format(**self.url_data)


class ApiLoader(PathMixin, VideoLoader):
    fields = set(['guid', 'link', 'title', 'description', 'files',
                  'embed_code', 'thumbnail_url', 'tags', 'publish_datetime',
                  'user', 'user_url', 'license'])

    def get_video_data(self, response):
        parsed = feedparser.parse(response.text.encode('utf-8'))
        return Suite.parse_feed_entry(parsed.entries[0])


class OEmbedLoader(OEmbedLoaderMixin, PathMixin, VideoLoader):
    endpoint = u"http://blip.tv/oembed/"
    # Technically, Blip would accept http://blip.tv/a/a-{post_id}, but we
    # shouldn't try to leverage that if we don't need to.
    new_url_format = u"http://blip.tv/{user}/{slug}-{post_id}"


class Feed(FeedparserFeed):
    """
    Supports the following known blip feeds:

    * blip.tv/rss: All most recent posts.
    * blip.tv/<show>/rss: Most recent posts by a show.

    Any of the following are valid inputs:

    * http://blip.tv/
    * http://blip.tv/rss
    * http://blip.tv?skin=rss
    * http://blip.tv/<show>
    * http://blip.tv/<show>/rss
    * http://blip.tv/<show>?skin=rss

    .. seealso:: http://wiki.blip.tv/index.php/Video_Browsing_API
                 http://wiki.blip.tv/index.php/RSS_Output_Format

    """
    path_re = re.compile(r'^(?:|/rss|(?:/(?P<show>[\w-]+))(?:/rss)?)/?$')
    page_url_format = "http://blip.tv/{show_path}rss?page={page}&pagelen=100"
    per_page = 100

    def get_url_data(self, url):
        parsed_url = urlparse.urlsplit(url)
        if parsed_url.scheme in ('http', 'https'):
            if parsed_url.netloc == 'blip.tv':
                match = self.path_re.match(parsed_url.path)
                if match:
                    return match.groupdict()

        raise UnhandledFeed(url)

    def get_page_url_data(self, *args, **kwargs):
        data = super(Feed, self).get_page_url_data(*args, **kwargs)
        show = self.url_data['show']
        data['show_path'] = '{0}/'.format(show) if show is not None else ''
        return data

    def get_video_data(self, item):
        if 'blip_puredescription' not in item:
            raise InvalidVideo
        return Suite.parse_feed_entry(item)


class Search(FeedparserSearch):
    page_url_format = "http://blip.tv/rss?page={page}&search={query}"
    # pagelen doesn't work with searches. Huh.
    per_page = 10

    def get_video_data(self, item):
        return Suite.parse_feed_entry(item)


class Suite(BaseSuite):
    loader_classes = (OEmbedLoader, ApiLoader)
    feed_class = Feed
    search_class = Search

    @staticmethod
    def parse_feed_entry(entry):
        """
        Parses a feedparser entry from a blip rss feed into a dictionary
        mapping :class:`.Video` fields to values. This is used for blip feeds
        and blip API requests (since those can also be done with feeds.)

        """
        files = [VideoFile(url=enclosure.get('url'),
                           mime_type=enclosure.get('type'),
                           length=(enclosure.get('filesize') or
                                   enclosure.get('length')))
                 for enclosure in get_accepted_enclosures(entry)]

        data = {
            'guid': entry['id'],
            'link': entry['link'],
            'title': entry['title'],
            'description': entry['blip_puredescription'],
            'files': files,
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


registry.register(Suite)
