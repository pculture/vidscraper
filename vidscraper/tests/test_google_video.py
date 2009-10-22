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

import unittest

from vidscraper.sites import google_video

BASE_URL = "http://video.google.com/videoplay?docid=3372610739323185039"

class GoogleVideoScrapingTestCase(unittest.TestCase):

    def test_scrape_title(self):
        """
        scrape_title() should return the title of the Google Video video.
        """
        self.assertEquals(google_video.scrape_title(BASE_URL),
                          "Tom and Jerry. Texas")

    def test_scrape_description(self):
        """
        scrape_description() should return the description HTML of the Google
        Video video.
        """
        self.assertEquals(google_video.scrape_description(BASE_URL),
                          "<p>Tom and Jerry. </p>")

    def test_scrape_file_url(self):
        """
        scrape_file_url() should return a URL to download the given Google
        Video video.
        """
        file_url = google_video.scrape_file_url(BASE_URL)
        self.assertTrue('googlevideo.com/videoplayback' in file_url)
        self.assertTrue('Tom+and+Jerry.+++Texas' in file_url)

    def test_file_url_is_flaky(self):
        """
        file_url_is_flaky() should return True because the URL from
        scrape_file_url() is not a permalink.
        """
        self.assertTrue(google_video.file_url_is_flaky(BASE_URL, {}))

    def test_scrape_embed_code(self):
        """
        scrape_embed_code() should return the HTML to embed the given Google
        Video video.
        """
        embed_code = """<embed id="VideoPlayback" \
src="http://video.google.com/googleplayer.swf?docid=3372610739323185039&\
hl=en&fs=true" style="width:400px;height:326px" allowFullScreen="true" \
allowScriptAccess="always" type="application/x-shockwave-flash"> </embed>"""
        self.assertEquals(google_video.scrape_embed_code(BASE_URL), embed_code)
