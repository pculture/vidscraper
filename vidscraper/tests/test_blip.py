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

from vidscraper.sites import blip

BASE_URL = "http://blip.tv/file/1754930"

class BlipTvScrapingTestCase(unittest.TestCase):

    def test_get_link(self):
        """
        get_link() should return a link to the webpage for the blip.tv video.
        """
        self.assertEquals(blip.get_link(BASE_URL), BASE_URL)

    def test_scrape_title(self):
        """
        scrape_title() should return the title of the blip.tv video.
        """
        self.assertEquals(blip.scrape_title(BASE_URL), "Miro 2.0 Introduction")

    def test_scrape_description(self):
        """
        scrape_description() should return the description HTML of the blip.tv
        video.
        """
        self.assertEquals(blip.scrape_description(BASE_URL), """<span><br>

New and improved, Miro 2.0!</span>""")

    def test_scrape_file_url(self):
        """
        scrape_file_url() should return a URL to download the given blip.tv
        video.
        """
        self.assertEquals(blip.scrape_file_url(BASE_URL),
                          "http://blip.tv/file/get/"
                          "Miropcf-Miro20Introduction189.mp4")

    def test_scrape_file_url_image(self):
        """
        scrape_file_url() should return None if the URL represents an image.
        """
        self.assertEquals(blip.scrape_file_url('http://blip.tv/file/728786'),
                          None)

    def test_get_embed(self):
        """
        get_embed() should return the HTML to embed the given blip.tv video.
        """
        embed_code = """<embed src="http://blip.tv/play/hMtu69JUAg" \
type="application/x-shockwave-flash" width="480" height="350" \
allowscriptaccess="always" allowfullscreen="true"></embed>"""
        self.assertEquals(blip.get_embed(BASE_URL), embed_code)

    def test_get_thumbnail_url(self):
        """
        get_thubmanil_url() should return the thumbnail URL for the blip.tv
        video.
        """
        self.assertEquals(blip.get_thumbnail_url(BASE_URL),
                          'http://a.images.blip.tv/'
                          'Miropcf-Miro20Introduction767.jpg')

    def test_scrape_pubish_date(self):
        """
        scrape_publish_date() should return a C{datetime.datetime} object of
        the date/time the video was originally published.
        """
        self.assertEquals(blip.scrape_publish_date(BASE_URL),
                          datetime.datetime(2009, 2, 9, 19, 42, 57))

    def test_get_tags(self):
        """
        get_tags() should return a list of the tags for the video.
        """
        self.assertEquals(blip.get_tags(BASE_URL),
                          ['Default Category'])

    def test_get_user(self):
        """
        get_user() should return the name of the blip.tv user who uploaded the
        video.
        """
        self.assertEquals(blip.get_user(BASE_URL),
                          'miropcf')

    def test_get_user_url(self):
        """
        get_user_url() should return the URL for the blip.tv user who uploaded
        the video.
        """
        self.assertEquals(blip.get_user_url(BASE_URL),
                          'http://miropcf.blip.tv/')
