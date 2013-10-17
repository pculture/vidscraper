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

import urlparse

import feedparser

from vidscraper.exceptions import UnhandledFeed
from vidscraper.suites import BaseSuite, registry
from vidscraper.utils.feedparser import (get_accepted_enclosures,
                                         struct_time_to_datetime)
from vidscraper.videos import FeedparserFeed, VideoFile


# add the Kaltura namespace to FeedParser.
# http://code.google.com/p/feedparser/issues/detail?id=55
feedparser._FeedParserMixin.namespaces[
    'http://kaltura.com/playlist/1.0'] = 'kaltura'


class Feed(FeedparserFeed):
    schemes = ('http', 'https')
    netlocs = ('kaltura.com', 'www.kaltura.com')
    path = '/index.php/partnerservices2/executeplaylist'
    page_url_format = ('http://www.kaltura.com/index.php/partnerservices2/'
                       'executeplaylist?format=8&partner_id={partner_id}'
                       '&subp_id={subp_id}&playlist_id={playlist_id}')

    def _next_page(self):
        if self.start_index != 1 or self.item_count > 0:
            raise StopIteration
        super(Feed, self)._next_page()

    def get_url_data(self, url):
        parsed_url = urlparse.urlsplit(url)
        if (parsed_url.scheme in self.schemes and
                parsed_url.netloc in self.netlocs and
                parsed_url.path == self.path):
            parsed_qs = urlparse.parse_qs(parsed_url.query)
            try:
                return {
                    'partner_id': parsed_qs['partner_id'][0],
                    'subp_id': parsed_qs['subp_id'][0],
                    'playlist_id': parsed_qs['playlist_id'][0],
                }
            except (KeyError, IndexError):
                pass

        raise UnhandledFeed(url)

    def get_video_data(self, item):
        files = [VideoFile(url=enclosure.get('url'),
                           mime_type=enclosure.get('type'),
                           length=(enclosure.get('filesize') or
                                   enclosure.get('length')))
                 for enclosure in get_accepted_enclosures(item)]

        data = {
            'title': item.title,
            'description': item.description,
            'thumbnail_url': item.media_thumbnail[0]['url'],
            'publish_datetime': struct_time_to_datetime(item.published_parsed),
            'user': item['kaltura_userscreenname'],
            'files': files or None,
        }
        return data


class Suite(BaseSuite):
    feed_class = Feed


registry.register(Suite)
