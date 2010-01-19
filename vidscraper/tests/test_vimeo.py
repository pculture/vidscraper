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
import feedparser
import unittest

from vidscraper.sites import vimeo
from vidscraper.bulk_import import vimeo as bulk_vimeo

BASE_URL = "http://vimeo.com/2"

class VimeoScrapingTestCase(unittest.TestCase):

    def test_scrape_title(self):
        """
        scrape_title() should return the title of the Vimeo video.
        """
        self.assertEquals(vimeo.scrape_title(BASE_URL),
                          "Good morning, universe")

    def test_scrape_description(self):
        """
        scrape_description() should return the description HTML of the Vimeo
        video.
        """
        self.assertEquals(vimeo.scrape_description(BASE_URL),
                          "<p>I shot this myself!</p>")

    def test_scrape_file_url(self):
        """
        scrape_file_url() should return a URL to download the given Vimeo
        video.
        """
        file_url = vimeo.scrape_file_url(BASE_URL)
        self.assertTrue(file_url.startswith(
                "http://www.vimeo.com/moogaloop/play/clip:2/"), file_url)

    def test_file_url_is_flaky(self):
        """
        file_url_is_flaky() should return True since the scrape_file_url()
        function does not return a stable URL.
        """
        self.assertEquals(vimeo.file_url_is_flaky(BASE_URL), True)

    def test_get_flash_enclosure_url(self):
        """
        get_flash_enclosure_url() should return a URL of a flash file for the
        Vimeo video.
        """
        self.assertEquals(vimeo.get_flash_enclosure_url(BASE_URL),
                          'http://vimeo.com/moogaloop.swf?clip_id=2')

    def test_get_embed(self):
        """
        get_embed() should return the HTML to embed the given Vimeo video.
        """
        embed_code = """<object width="425" height="344">\
<param name="allowfullscreen" value="true">\
<param name="allowscriptaccess" value="always">\
<param name="movie" value="\
http://vimeo.com/moogaloop.swf?show_byline=1&amp;fullscreen=1&amp;clip_id=2\
&amp;color=&amp;server=vimeo.com&amp;show_title=1&amp;show_portrait=0">\
<embed src="http://vimeo.com/moogaloop.swf?show_byline=1&amp;fullscreen=1&amp;\
clip_id=2&amp;color=&amp;server=vimeo.com&amp;show_title=1&amp;\
show_portrait=0" allowscriptaccess="always" height="344" width="425" \
allowfullscreen="true" type="application/x-shockwave-flash"></embed>\
</object>"""
        self.assertEquals(vimeo.get_embed(BASE_URL), embed_code)

    def test_get_thumbnail_url(self):
        """
        get_thubmanil_url() should return the thumbnail URL for the Vimeo
        video.
        """
        self.assertTrue(vimeo.get_thumbnail_url(BASE_URL).endswith(
                '228/979/22897998_640.jpg'))

    def test_scrape_pubish_date(self):
        """
        scrape_publish_date() should return a C{datetime.datetime} object of
        the date/time the video was originally published.
        """
        self.assertEquals(vimeo.scrape_publish_date(BASE_URL),
                          datetime.datetime(2005, 2, 16, 23, 9, 19))

    def test_get_user(self):
        """
        get_user() should return the name of the Vimeo user who uploaded the
        video.
        """
        self.assertEquals(vimeo.get_user(BASE_URL),
                          'Jake Lodwick')

    def test_get_user_url(self):
        """
        get_user_url() should return the URL for the Vimeo user who uploaded
        the video.
        """
        self.assertEquals(vimeo.get_user_url(BASE_URL),
                          'http://vimeo.com/jakob')


class VimeoBulkImportTestCase(unittest.TestCase):

    url = "http://www.vimeo.com/snippets/videos/rss"
    parsed_feed = feedparser.parse(url)

    def test_video_count(self):
        """
        video_count() should return the number of videos total in the Vimeo
        feed.
        """
        self.assertEquals(bulk_vimeo.video_count(self.parsed_feed),
                          90)

    def test_bulk_import(self):
        """
        bulk_import() should return a FeedParser dict with all of the videos
        from the feed.
        """
        big_parsed = bulk_vimeo.bulk_import(self.parsed_feed)
        self.assertEquals(len(big_parsed.entries), 90)
        self.assertEquals(big_parsed.entries[0].title, 'Favorite Songs')
        self.assertEquals(big_parsed.entries[-1].title, 'First Snippet')
