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

from vidscraper.sites import fora

BASE_URL = ("http://fora.tv/2009/04/28/"
            "Stefan_Ingves_Monetary_Policy_in_a_Financial_Crisis")

class ForaTvScrapingTestCase(unittest.TestCase):

    def test_scrape_link(self):
        """
        scrape_link() should return a link to the webpage for the Fora.tv
        video.
        """
        self.assertEquals(fora.scrape_link(BASE_URL), BASE_URL)

    def test_scrape_title(self):
        """
        scrape_title() should return the title of the Fora.tv video.
        """
        self.assertEquals(
            fora.scrape_title(BASE_URL),
            "Stefan Ingves: Monetary Policy in a Financial Crisis")

    def test_scrape_description(self):
        """
        scrape_description() should return the description HTML of the Fora.tv
        video.
        """
        self.assertEquals(fora.scrape_description(BASE_URL),
                          "Failing banks, frozen credit markets, a faltering "
                          "economy ... sound familiar? That was the situation "
                          "in Sweden in the early 1990s. One of the key "
                          "architects of the Swedish government's response "
                          "was Stefan Ingves, who gives this talk at Duke "
                          "University.")

    def test_get_embed(self):
        """
        get_embed() should return the HTML to embed the given Fora.tv video.
        """
        embed_code = """<object width="400" height="264">\
<param name="flashvars"\
 value="webhost=fora.tv&amp;clipid=9595&amp;cliptype=full&amp;ie=f"/>\
<param name="movie" value="http://fora.tv/embedded_player"/>\
<param name="allowFullScreen" value="true"/>\
<param name="allowscriptaccess" value="always"/>\
<embed src="http://fora.tv/embedded_player" allowscriptaccess="always"\
 height="264" width="400" allowfullscreen="true"\
 type="application/x-shockwave-flash"\
 flashvars="webhost=fora.tv&amp;clipid=9595&amp;cliptype=full&amp;ie=f"/>\
</object>"""
        self.assertEquals(fora.get_embed(BASE_URL), embed_code)

    def test_scrape_flash_enclosure_url(self):
        """
        scrape_flash_enclosure_url() should return the canonical URL of the
        Fora.tv video page.
        """
        self.assertEquals(fora.scrape_flash_enclosure_url(BASE_URL),
                          "http://fora.tv/embedded_player?webhost=fora.tv&"
                          "clipid=9595&cliptype=clip&ie=f")

    def test_scrape_thumbnail_url(self):
        """
        scrape_thubmanil_url() should return the thumbnail URL for the Fora.tv
        video.
        """
        self.assertEquals(fora.scrape_thumbnail_url(BASE_URL),
                          'http://fora.tv/media/thumbnails/9595_320_240.jpg')

    def test_scrape_publish_date(self):
        """
        scrape_publish_date() should return a C{datetime.datetime} object of
        the date/time the video was originally published.
        """
        self.assertEquals(fora.scrape_publish_date(BASE_URL),
                          datetime.datetime(2009, 4, 28, 0, 0, 0))

    def test_scrape_user(self):
        """
        scrape_user() should return the name of the Fora.tv user who uploaded
        the video.
        """
        self.assertEquals(fora.scrape_user(BASE_URL),
                          'Duke University')

    def test_scrape_user_url(self):
        """
        scrape_user_url() should return the URL for the Fora.tv user who
        uploaded the video.
        """
        self.assertEquals(fora.scrape_user_url(BASE_URL),
                          'http://fora.tv/partner/Duke_University')
