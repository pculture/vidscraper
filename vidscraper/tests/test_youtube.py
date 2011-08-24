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

from vidscraper import errors
from vidscraper.sites import youtube

BASE_URL = "http://www.youtube.com/watch?v=oHg5SJYRHA0"
BASE_URL_SHORT = "http://youtu.be/oHg5SJYRHA0"

class YoutubeScrapingTestCase(unittest.TestCase):

    def test_canonical_url(self):
        """
        canonical_url() should return the simplest URL for a given YouTube URL.
        If the URL is already canonical, it should not be changed.
        """

        self.assertEquals(youtube.canonical_url(BASE_URL),
                          BASE_URL)
        for long_url in [BASE_URL + '&feature=popular',
                         BASE_URL + '&feature=channel',
                         BASE_URL + '&feature=youtube_gdata',
                         BASE_URL + '&list=UL']:
            self.assertEquals(youtube.canonical_url(long_url),
                              BASE_URL)

        # short URL
        self.assertEquals(youtube.canonical_url(BASE_URL_SHORT),
                          BASE_URL)

    def test_regex(self):
        """
        YOUTUBE_REGEX shoud match YouTube video URLs, and not other URLs.
        """
        for url, match in (
            (BASE_URL, True),
            (BASE_URL + '&feature=popular', True),
            ('https://youtube.com/?feature=popular&v=foo', True),
            (BASE_URL_SHORT, True),
            ('http://www.youtube.com/', False),
            ('http://youtube.com/foo', False),
            ('http://www.google.com/?v=foo', False)):
            self.assertEquals(bool(youtube.YOUTUBE_REGEX.match(url)),
                              match, 'match(%s) != %s' % (url, match))

    def test_get_link(self):
        """
        get_link() should return a link to the webpage for the YouTube video.
        """
        self.assertEquals(youtube.get_link(BASE_URL), BASE_URL)
        self.assertEquals(youtube.get_link(BASE_URL_SHORT), BASE_URL)

    def test_scrape_title(self):
        """
        scrape_title() should return the title of the YouTube video.
        """
        self.assertEquals(youtube.scrape_title(BASE_URL), "RickRoll'D")
        self.assertEquals(youtube.scrape_title(BASE_URL_SHORT), "RickRoll'D")

    def test_scrape_description(self):
        """
        scrape_description() should return the description HTML of the YouTube
        video.
        """
        description =  """http://www.facebook.com/rickroll548"""
        self.assertEquals(youtube.scrape_description(BASE_URL), description)
        self.assertEquals(youtube.scrape_description(BASE_URL_SHORT),
                          description)

    def test_get_embed(self):
        """
        get_embed() should return the HTML to embed the given YouTube video.
        """
        embed_code = """<object width="425" height="344">\
<param name="movie"\
 value="http://www.youtube.com/v/oHg5SJYRHA0?f=videos&amp;app=youtube_gdata">\
<param name="allowFullScreen" value="true">\
<param name="allowscriptaccess" value="always">\
<embed\
 src="http://www.youtube.com/v/oHg5SJYRHA0?f=videos&amp;app=youtube_gdata"\
 allowscriptaccess="always" height="344" width="425" allowfullscreen="true"\
 type="application/x-shockwave-flash"></embed></object>"""
        self.assertEquals(youtube.get_embed(BASE_URL), embed_code)
        self.assertEquals(youtube.get_embed(BASE_URL_SHORT), embed_code)

    def test_get_flash_enclosure_url(self):
        """
        get_flash_enclosure_url() should return the canonical URL of the
        YouTube video page.
        """
        self.assertEquals(youtube.get_flash_enclosure_url(BASE_URL),
                          BASE_URL)
        self.assertEquals(youtube.get_flash_enclosure_url(BASE_URL_SHORT),
                          BASE_URL)

    def test_get_thumbnail_url(self):
        """
        get_thubmanil_url() should return the thumbnail URL for the YouTube
        video.
        """
        self.assertEquals(youtube.get_thumbnail_url(BASE_URL),
                          'http://img.youtube.com/vi/oHg5SJYRHA0/'
                          'hqdefault.jpg')
        self.assertEquals(youtube.get_thumbnail_url(BASE_URL_SHORT),
                          'http://img.youtube.com/vi/oHg5SJYRHA0/'
                          'hqdefault.jpg')

    def test_scrape_published_date(self):
        """
        scrape_published_date() should return a C{datetime.datetime} object of
        the date/time the video was originally published.
        """
        self.assertEquals(youtube.scrape_published_date(BASE_URL),
                          datetime.datetime(2007, 5, 15, 7, 21, 50))
        self.assertEquals(youtube.scrape_published_date(BASE_URL_SHORT),
                          datetime.datetime(2007, 5, 15, 7, 21, 50))

    def test_get_tags(self):
        """
        get_tags() should return a list of the tags for the video.
        """
        self.assertEquals(set(youtube.get_tags(BASE_URL)),
                          set("Cotter548 Shawn Cotter lol gamefaqs CE no brb "
                              "afk lawl pwnt Rickroll Rickroll'd Rick Roll "
                              "Music Duckroll Duck astley never gonna "
                              "give you up let down run around and "
                              "hurt".split()))
        self.assertEquals(set(youtube.get_tags(BASE_URL_SHORT)),
                          set("Cotter548 Shawn Cotter lol gamefaqs CE no brb "
                              "afk lawl pwnt Rickroll Rickroll'd Rick Roll "
                              "Music Duckroll Duck astley never gonna "
                              "give you up let down run around and "
                              "hurt".split()))

    def test_get_user(self):
        """
        get_user() should return the name of the YouTube user who uploaded the
        video.
        """
        self.assertEquals(youtube.get_user(BASE_URL),
                          'cotter548')
        self.assertEquals(youtube.get_user(BASE_URL_SHORT),
                          'cotter548')

    def test_get_user_url(self):
        """
        get_user_url() should return the URL for the YouTube user who uploaded
        the video.
        """
        self.assertEquals(youtube.get_user_url(BASE_URL),
                          'http://www.youtube.com/user/cotter548')
        self.assertEquals(youtube.get_user_url(BASE_URL_SHORT),
                          'http://www.youtube.com/user/cotter548')

    def test_is_embedable(self):
        """
        is_embedable() should return True if the URL is embedable, False
        otherwise.
        """
        self.assertTrue(youtube.is_embedable(BASE_URL))
        self.assertFalse(youtube.is_embedable(
                "http://www.youtube.com/watch?v=6TT19cB0NTM"))


    def test_provide_api_short_url(self):
        """
        If a short URL is given (http://youtu.be/foo), provide API should still
        parse the feed.
        """
        def _(url, shortmem):
            self.assertTrue('base_etree' in shortmem)
            return True
        self.assertTrue(youtube.provide_api(_)(
                'http://youtu.be/oHg5SJYRHA0', {}))

    def test_provide_api_invalid_url(self):
        """
        If an unknown URL is accessed, the provide_api decorator should raise
        BaseUrlLoadFailure.
        """
        func = youtube.provide_api(lambda x, shortmem: True)
        self.assertRaises(
            errors.BaseUrlLoadFailure, func,
            'http://www.youtube.com/watch?v=-1', {})

    def test_provide_api_private_url(self):
        """
        If an private URL is accessed, the provide_api decorator should raise
        VideoDeleted.
        """
        func = youtube.provide_api(lambda x, shortmem: True)
        self.assertRaises(
            errors.VideoDeleted, func,
            'http://www.youtube.com/watch?v=Vbvf1Q3DrPY', {})

    def test_provide_api_deleted_video(self):
        """
        If a deleted URL is accessed, the provide_api decorator should raise
        VideoDeleted.
        """
        func = youtube.provide_api(lambda x, shortmem: True)
        self.assertRaises(
            errors.VideoDeleted, func,
            'http://www.youtube.com/watch?v=vLdfSn2xr-Q', {})
