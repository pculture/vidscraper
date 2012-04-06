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
import urlparse

import feedparser

from vidscraper.exceptions import UnhandledURL, UnhandledSearch
from vidscraper.suites import BaseSuite, registry, SuiteMethod, OEmbedMethod
from vidscraper.utils.feedparser import get_entry_thumbnail_url, \
                                        get_first_accepted_enclosure
from vidscraper.utils.http import clean_description_html
from vidscraper.videos import FeedparserVideoFeed, FeedparserVideoSearch


class BlipApiMethod(SuiteMethod):
    fields = set(['guid', 'link', 'title', 'description', 'file_url',
                  'embed_code', 'thumbnail_url', 'tags', 'publish_datetime',
                  'user', 'user_url', 'license'])

    def get_url(self, video):
        parsed_url = urlparse.urlsplit(video.url)
        new_match = BlipSuite.new_video_path_re.match(parsed_url.path)
        if new_match:
            post_id = int(new_match.group('post_id'))
            new_parsed_url = parsed_url[:2] + ("/rss/%d" % post_id, None,
                                               None)
        elif BlipSuite.old_video_path_re.match(parsed_url.path):
            new_parsed_url = parsed_url[:3] + ("skin=rss", None)
        else:
            # We shouldn't ever get here, so raise an exception.
            raise UnhandledURL(video.url)

        return urlparse.urlunsplit(new_parsed_url)

    def process(self, response):
        parsed = feedparser.parse(response.text.encode('utf-8'))
        return BlipSuite.parse_feed_entry(parsed.entries[0])


class BlipFeed(FeedparserVideoFeed):
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

        raise UnhandledURL(url)

    def get_page_url_data(self, *args, **kwargs):
        data = super(BlipFeed, self).get_page_url_data(*args, **kwargs)
        show = self.url_data['show']
        data['show_path'] = '{0}/'.format(show) if show is not None else ''
        return data

    def get_item_data(self, item):
        return BlipSuite.parse_feed_entry(item)


class BlipSearch(FeedparserVideoSearch):
    page_url_format = "http://blip.tv/rss?page={page}&search={query}"
    # pagelen doesn't work with searches. Huh.
    per_page = 10

    def get_item_data(self, item):
        return BlipSuite.parse_feed_entry(item)


class BlipSuite(BaseSuite):
    video_regex = r'^https?://(?P<subsite>[a-zA-Z]+\.)?blip.tv(?:/.*)?(?<!.mp4)$'
    feed_regex = video_regex

    new_video_path_re = re.compile(r'^/[\w-]+/[\w-]+-(?P<post_id>\d+)/?$')
    old_video_path_re = re.compile(r'^/file/\d+/?$', re.I)

    methods = (OEmbedMethod(u"http://blip.tv/oembed/"), BlipApiMethod())

    feed_class = BlipFeed
    search_class = BlipSearch

    def handles_video_url(self, url):
        parsed_url = urlparse.urlsplit(url)
        if parsed_url.scheme not in ('http', 'https'):
            return False

        if (not parsed_url.netloc == 'blip.tv' and
            not parsed_url.netloc.endswith('.blip.tv')):
            return False

        if (self.new_video_path_re.match(parsed_url.path) or
            self.old_video_path_re.match(parsed_url.path)):
            return True

        return False

    @staticmethod
    def parse_feed_entry(entry):
        """
        Parses a feedparser entry from a blip rss feed into a dictionary
        mapping :class:`.Video` fields to values. This is used for blip feeds
        and blip API requests (since those can also be done with feeds.)

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


registry.register(BlipSuite)
