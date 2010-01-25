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
import unittest

from vidscraper import scrape_suite
from vidscraper.sites import ustream

BASE_URL = "http://www.ustream.tv/recorded/2273554"

class UStreamScrapingTestCase(unittest.TestCase):

    def test_get_link(self):
        """
        get_link() should return a link to the webpage for the uStream
        video.
        """
        self.assertEquals(ustream.get_link(BASE_URL), BASE_URL)

    def test_get_title(self):
        """
        get_title() should return the title of the uStream video.
        """
        self.assertEquals(
            ustream.get_title(BASE_URL),
            "Prospects in Public Health: "
            "a Conversation with Gail Rosseau & John Harwood (Part 2 of 2)")

    def test_get_description(self):
        """
        get_description() should return the description HTML of the uStream
        video.
        """
        self.assertEquals(ustream.get_description(BASE_URL),
                          u"Terry Sanford Distinguished Lecturer Gail Rosseau "
                          u"in dialogue with John Harwood T\u201978 of The "
                          u"New York Times and CNBC.")

    def test_get_embed(self):
        """
        get_embed() should return the HTML to embed the given uStream video.
        """
        embed_code = """<embed flashvars="autoplay=false" width="320"\
 height="260" allowfullscreen="true" allowscriptaccess="always"\
 src="http://www.ustream.tv/flash/video/2273554"\
 type="application/x-shockwave-flash" />"""
        self.assertEquals(ustream.get_embed(BASE_URL), embed_code)

    def test_get_flash_enclosure_url(self):
        """
        get_flash_enclosure_url() should return the canonical URL of the
        uStream video page.
        """
        self.assertEquals(ustream.get_flash_enclosure_url(BASE_URL),
                          "http://www.ustream.tv/flash/video/2273554")

    def test_get_thumbnail_url(self):
        """
        get_thubmanil_url() should return the thumbnail URL for the uStream
        video.
        """
        self.assertEquals(ustream.get_thumbnail_url(BASE_URL),
                          'http://static-cdn1.ustream.tv/videopic/0/1/2/2273/'
                          '2273554/1_776545_2273554_320x240_b_1:1.jpg')

    def test_get_publish_date(self):
        """
        get_publish_date() should return a C{datetime.datetime} object of
        the date/time the video was originally published.
        """
        self.assertEquals(ustream.get_publish_date(BASE_URL),
                          datetime.datetime(2009, 10, 3, 7, 53, 44))

    def test_get_user(self):
        """
        get_user() should return the name of the uStream user who uploaded
        the video.
        """
        self.assertEquals(ustream.get_user(BASE_URL),
                          'dukeuniversity')

    def test_get_user_url(self):
        """
        get_user_url() should return the URL for the uStream user who
        uploaded the video.
        """
        self.assertEquals(ustream.get_user_url(BASE_URL),
                          'http://www.ustream.tv/dukeuniversity')

    def test_scrape_removed_video(self):
        """
        A removed video should return a blank dictionary.
        """
        self.assertEquals(
            scrape_suite('http://www.ustream.tv/recorded/4155845',
                         ustream.SUITE),
            {})
