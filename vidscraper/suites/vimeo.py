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

from vidscraper.compat import json
from vidscraper.suites import BaseSuite, registry


class VimeoSuite(BaseSuite):
    """
    Suite for vimeo.com. Currently supports their oembed api and simple api. No
    API key is required for this level of access.

    """
    video_regex = r'https?://([^/]+\.)?vimeo.com/(?P<video_id>\d+)'
    feed_regex = r'https?://([^/]+\.)?vimeo.com/'
    _tag_re = re.compile(r'>([\w ]+)</a>')

    api_fields = set(['link', 'title', 'description', 'tags', 'publish_date', 'thumbnail_url', 'user', 'user_url', 'flash_enclosure_url', 'embed_code'])
    oembed_endpoint = u"http://vimeo.com/api/oembed.json"

    def get_api_url(self, video):
        video_id = self.video_regex.match(video.url).group('video_id')
        return u"http://vimeo.com/api/v2/video/%s.json" % video_id

    def parse_api_response(self, response_text):
        parsed = json.loads(response_text)[0]
        flash_enclosure_url = 'http://vimeo.com/moogaloop.swf?clip_id=%s' % (
                              parsed['id'])
        embed_code = u"""<iframe src="http://player.vimeo.com/video/%s" \
width="320" height="240" frameborder="0" webkitAllowFullScreen \
allowFullScreen></iframe>""" % parsed['id']
        data = {
            'title': parsed['title'],
            'link': parsed['url'],
            'description': parsed['description'],
            'thumbnail_url': parsed['thumbnail_medium'],
            'user': parsed['user_name'],
            'user_url': parsed['user_url'],
            'publish_date': datetime.strptime(parsed['upload_date'],
                                             '%Y-%m-%d %H:%M:%S'),
            'tags': parsed['tags'].split(', '),
            'flash_enclosure_url': flash_enclosure_url,
            'embed_code': embed_code
        }
        return data

    def parse_feed_entry(self, entry, fields=None):
        description = entry['summary']
        description, tag_str = description.split("<p><strong>Tags:</strong>")
        tags = [match.group(1) for match in self._tag_re.finditer(tag_str)]
        data = {
            'link': entry['link'],
            'title': entry['title'],
            'description': description,
            'publish_datetime': datetime(*entry['updated_parsed'][:6]),
            'user': entry['author'],
            'user_url': entry['media_credit']['scheme'],
            'thumbnail_url': entry['media_thumbnail'][0]['url'],
            'flash_enclosure_url': entry['media_player']['url'],
            'tags': tags,
        }
        print data['thumbnail_url']
        video = self.get_video(data['link'], fields)
        for field, value in data.iteritems():
            if field in video.fields:
                setattr(video, field, value)
        return video
registry.register(VimeoSuite)
