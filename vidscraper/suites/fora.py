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
import urllib
import urlparse

from BeautifulSoup import BeautifulSoup, SoupStrainer

from vidscraper.suites import BaseSuite, registry
from vidscraper.utils.html import make_embed_code


CONTENT_IDS = set(['program_title_text',])
CONTENT_CLASSES = set(['partner_header', 'information_left', 'description'])
CONTENT_RELS = set(['image_src', 'video_src', 'canonical'])


def _strain_filter(name, attrs):
    return any((attr[0] == 'id' and attr[1] in CONTENT_IDS or
        attr[0] == 'class' and attr[1] in CONTENT_CLASSES or
        attr[0] == 'rel' and attr[1] in CONTENT_RELS
        for attr in attrs))


class ForaSuite(BaseSuite):
    """Suite for fora.tv. As of 19-09-2011 fora does not offer any public API, only video pages and rss feeds."""
    video_regex = 'https?://(www\.)?fora\.tv/\d{4}/\d{2}/\d{2}/\w+'
    scrape_fields = set(['link', 'title', 'description', 'flash_enclosure_url', 'embed_code', 'thumbnail_url', 'publish_date', 'user', 'user_url'])

    def get_scrape_url(self, video):
        return video.url

    def parse_scrape_response(self, response_text):
        strainer = SoupStrainer(_strain_filter)
        soup = BeautifulSoup(response_text, parseOnlyThese=strainer)
        data = {}
        for tag in soup:
            if tag.name == 'link':
                if tag['rel'] == 'image_src':
                    data['thumbnail_url'] = unicode(tag['href'])
                elif tag['rel'] == 'video_src':
                    src = unicode(tag['href'])
                    data['flash_enclosure_url'] = src
                    flash_url, flash_vars = src.split('?', 1)
                    flash_vars = urlparse.parse_qs(flash_vars)
                    flash_vars['cliptype'] = 'full'
                    flash_vars = urllib.urlencode(flash_vars)
                    data['embed_code'] = make_embed_code(flash_url, flash_vars)
                elif tag['rel'] == 'canonical':
                    data['link'] = u"http://fora.tv%s" % unicode(tag['href'])
            elif tag.name == 'span' and tag['id'] == 'program_title_text':
                data['title'] = unicode(tag.string)
            elif tag.name == 'dd' and tag['class'] == 'description':
                data['description'] = ''.join((unicode(t) for t in tag)).strip()
            elif tag.name == 'a' and tag['class'] == 'partner_header':
                data['user'] = unicode(tag.string)
                data['user_url'] = unicode(tag['href'])
            elif tag.name == 'div' and tag['class'] == 'information_left':
                dds = tag.findAll('dd')
                date = unicode(dds[2].string)
                date = datetime.datetime.strptime(date, "%m.%d.%y")
                data['publish_date'] = date
        return data
registry.register(ForaSuite)
