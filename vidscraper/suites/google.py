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

from BeautifulSoup import BeautifulSoup

from vidscraper.suites import BaseSuite, registry


ID_REGEX = re.compile(r'video-title|video-description|embed-video-code')


class GoogleSuite(BaseSuite):
    """Suite for scraping video pages from videos.google.com"""
    video_regex = r'^https?://video.google.com/videoplay'
    scrape_fields = set(['title', 'description', 'embed_code'])

    def get_scrape_url(self, video):
        return video.url

    def parse_scrape_response(self, response_text):
        soup = BeautifulSoup(response_text).findAll(attrs={'id': ID_REGEX})
        data = {}
        for tag in soup:
            if tag['id'] == 'video-title':
                data['title'] = unicode(tag.string)
            elif tag['id'] == 'video-description':
                data['description'] = ''.join((unicode(t) for t in tag)).strip()
            elif tag['id'] == 'embed-video-code':
                # This isn't the cleanest way of handling the gt/lt problem,
                # but this is a scrape and liable to break anyway. KISS.
                data['embed_code'] = unicode(tag.string).replace("&gt;", ">").replace("&lt;", "<")
        return data
registry.register(GoogleSuite)
