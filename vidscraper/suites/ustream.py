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
import json
import re
import urlparse

from vidscraper.exceptions import UnhandledURL
from vidscraper.suites import BaseSuite, registry
from vidscraper.videos import VideoLoader, OEmbedLoaderMixin


class UstreamPathMixin(object):
    path_re = re.compile(r'/recorded/(?P<id>\d+)/?$')

    def get_url_data(self, url):
        parsed_url = urlparse.urlsplit(url)
        if (parsed_url.scheme in ('http', 'https') and
            parsed_url.netloc in ('ustream.tv', 'www.ustream.tv')):
            match = self.path_re.match(parsed_url.path)
            if match:
                return match.groupdict()
        raise UnhandledURL(url)


class UstreamApiLoader(UstreamPathMixin, VideoLoader):
    fields = set(['link', 'title', 'description', 'flash_enclosure_url',
                  'embed_code', 'thumbnail_url', 'publish_date', 'tags',
                  'user', 'user_url'])

    url_format = u'http://api.ustream.tv/json/video/{id}/getInfo/?key={ustream_key}'

    def get_url_data(self, url):
        if 'ustream_key' not in self.api_keys:
            raise UnhandledURL(url)
        data = super(UstreamApiLoader, self).get_url_data(url)
        data.update(self.api_keys)
        return data

    def get_video_data(self, response):
        parsed = json.loads(response.text)['results']
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


class UstreamOEmbedLoader(OEmbedLoaderMixin, UstreamPathMixin, VideoLoader):
    endpoint = "http://www.ustream.tv/oembed/"
    url_format = "http://www.ustream.tv/recorded/{id}"


class UstreamSuite(BaseSuite):
    """Suite for fetching data on ustream videos."""
    # TODO: Ustream has feeds and search functionality - add support for that!
    loader_classes = (UstreamOEmbedLoader, UstreamApiLoader)


registry.register(UstreamSuite)
