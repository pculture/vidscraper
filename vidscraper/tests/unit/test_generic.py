# -*- coding: utf-8 -*-
# Copyright 2011 - Participatory Culture Foundation
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

from vidscraper.suites.generic import Suite
from vidscraper.tests.base import BaseTestCase
from vidscraper.videos import VideoFile


class SuiteTestCase(BaseTestCase):
    def setUp(self):
        self.suite = Suite()
        self.feed = self.suite.get_feed(
            'file://{0}'.format(self._data_file_path('generic/feed.rss')))
        self.old_SANITIZE = feedparser.SANITIZE_HTML
        feedparser.SANITIZE_HTML = False

    def tearDown(self):
        feedparser.SANITIZE_HTML = self.old_SANITIZE

    def test_basic_feed_data(self):
        # this test can be removed if base unit tests for the feedparser mixin
        # get added.
        self.feed.load()
        self.assertEqual(self.feed.title, 'Internet Archive - Mediatype: movies')
        self.assertEqual(self.feed.webpage, 'http://www.archive.org/details/movies')
        self.assertEqual(
            self.feed.description,
            ('The most recent additions to the Internet Archive collections.  '
             'This RSS feed is generated dynamically'))
        self.assertEqual(self.feed.last_modified,
                         datetime.datetime(2011, 10, 20, 14, 36, 1))
        self.assertEqual(self.feed.video_count, 2)
        
    def test_get_video_data(self):
        video = self.feed.next()
        self.assertEqual(video.title,
                         'SFGTV : October 20, 2011 6:00am-6:30am PDT')
        self.assertEqual(
            video.description,
            """<img \
src="http://www.archive.org/services/get-item-image.php?identifier=\
SFGTV_20111020_130000&amp;mediatype=movies&amp;collection=TV-SFGTV" \
style="padding-right:3px;float:left;" width="160" />\
<p>No description available.</p>\
<p>This item belongs to: movies/TV-SFGTV.</p>\
<p>This item has files of the following types: Animated GIF, Closed Caption \
Text, MP3, MPEG2, Metadata, SubRip, Thumbnail, Video Index, h.264</p>""")
        self.assertEqual(
            video.link,
            "http://www.archive.org/details/SFGTV_20111020_130000")
        self.assertEqual(
            video.thumbnail_url,
            ("http://www.archive.org/download/"
             "SFGTV_20111020_130000/format=Thumbnail"))
        self.assertEqual(
            video.files[0].url,
            ("http://www.archive.org/download/"
             "SFGTV_20111020_130000/format=h.264"))
        self.assertEqual(video.files[0].mime_type, "video/h264")
        self.assertEqual(video.publish_datetime,
                         datetime.datetime(2011, 10, 20, 14, 14, 14))
        self.assertEqual(video.license,
                         'http://creativecommons.org/licenses/by/2.5/')

    def test_feed_entry_unicode(self):
        # skip the first video.
        self.feed.next()
        video = self.feed.next()
        self.assertEqual(
            video.title,
            u'مصر الجديدة - الشيخ خالد عبد الله " 19-10-2011 "')
        self.assertEqual(
            video.description,
            u"""<img \
src="http://www.archive.org/services/get-item-image.php?identifier=\
forsan2011-2196&amp;mediatype=movies&amp;collection=opensource_movies" \
style="padding-right:3px;float:left;" width="160" />\
<p>منتدى فرسان السنة - فرسان الحقـ www.forsanelhaq.com ____________________ \
مصر الجديدة - الشيخ خالد عبد الله " 19-10-2011 ".</p>\
<p>This item belongs to: movies/opensource_movies.</p>\
<p>This item has files of the following types: Animated GIF, Cinepack, \
Metadata, Ogg Video, Ogg Vorbis, Thumbnail, VBR MP3, Windows Media Audio, \
h.264</p>""")
        self.assertEqual(
            video.link,
            "http://www.archive.org/details/forsan2011-2196")
        self.assertEqual(
            video.thumbnail_url,
            ("http://www.archive.org/download/"
             "forsan2011-2196/format=Thumbnail"))
        self.assertEqual(
            video.files[0].url,
            ("http://www.archive.org/download/"
             "forsan2011-2196/format=h.264"))
        self.assertEqual(video.files[0].mime_type, "video/h264")
        self.assertEqual(video.publish_datetime,
                         datetime.datetime(2011, 10, 20, 14, 17, 44))

    def test_parse_feed_entry_rel_via(self):
        fp = feedparser.parse(self._data_file_path('generic/feed_with_link_via.atom'))
        data = self.feed.get_video_data(fp.entries[0])
        self.assertEqual(data['link'],
                         "http://www.example.org/entries/1")

    def test_parse_feed_entry_atom(self):
        fp = feedparser.parse(self._data_file_path('generic/feed.atom'))
        data = self.feed.get_video_data(fp.entries[0])
        self.assertEqual(
            data,
            {'title': u'Atom 1.0',
             'description': u"""<h1>Show Notes</h1>
        <ul>
          <li>00:01:00 -- Introduction</li>
          <li>00:15:00 -- Talking about Atom 1.0</li>
          <li>00:30:00 -- Wrapping up</li>
        </ul>""",
             'tags': None,
             'link': u'http://www.example.org/entries/1',
             'guid': u'http://www.example.org/entries/1',
             'embed_code': None,
             'files': [VideoFile(
                        url=u'http://www.example.org/myvideo.ogg',
                        length=u'1234',
                        mime_type=u'application/ogg')],
             'thumbnail_url': None,
             'publish_datetime': datetime.datetime(2005, 7, 15, 12, 0),
             'license': 'http://creativecommons.org/licenses/by/2.5/'})

    def test_parse_feed_media_player(self):
        fp = feedparser.parse(self._data_file_path('generic/feed_with_media_player.atom'))
        data = self.feed.get_video_data(fp.entries[0])
        self.assertEqual(data['embed_code'],
                         u'<object width="425" height="271">'
                         '<embed id="ONPlayerEmbed" width="425" height="271" '
                         'allowfullscreen="true" flashvars="configFileName='
                         'http://www.onnetworks.com/embed_player/videos/'
                         'smart-girls-at-the-party/the-dancer-kenaudra?'
                         'target=site" scale="aspect" '
                         'allowscriptaccess="always" allownetworking="all" '
                         'quality="high" bgcolor="#ffffff" name="ONPlayer" '
                         'style="" src="http://www.onnetworks.com/swfs/'
                         'ONPlayerEmbed.swf/product_id=sgatp_0108_kenaudra/'
                         'cspid=4b2678259ccf1f2b" '
                         'type="application/x-shockwave-flash"></embed>'
                         '</object>')

    def test_parse_feed_media_content(self):
        fp = feedparser.parse(self._data_file_path('generic/feed_with_media_content.rss'))
        data = self.feed.get_video_data(fp.entries[0])
        video_file = data['files'][0]
        self.assertEqual(
            video_file.url,
            'http://videos.stupidvideos.com/2/00/40/30/51/403051.flv')
        self.assertEqual(video_file.mime_type, 'video/x-flv')
        self.assertEqual(data['embed_code'], None)

    def test_parse_feed_media_player_url(self):
        """
        Because the media:player doesn't have any content, and this entry has
        an enclosure, we don't use the media:player attribute.
        """
        fp = feedparser.parse(self._data_file_path('generic/feed_with_media_player_url.rss'))
        data = self.feed.get_video_data(fp.entries[0])
        video_file = data['files'][0]
        self.assertEqual(video_file.url, 'http://vimeo.com/moogaloop.swf?clip_id=7981161')
        self.assertEqual(video_file.mime_type, 'application/x-shockwave-flash')
        self.assertEqual(video_file.length, '15993252')
        self.assertEqual(data['embed_code'], None)

    def test_entry_no_title(self):
        """
        If one of the entries is missing a title, the feed should be able to
        parse data out of it (rather than choking).

        """
        fp = feedparser.parse(self._data_file_path('generic/garbage.rss'))
        entry = fp.entries[3]
        self.assertTrue('title' not in entry)
        data = self.feed.get_video_data(entry)

    def test_entry_invalid_date(self):
        """
        If one of the entries has an unparseable publish date, the feed
        shouldn't choke on that.

        """
        fp = feedparser.parse(self._data_file_path('generic/invalid_dates.rss'))
        entry = fp.entries[0]
        self.assertTrue('published_parsed' in entry)
        self.assertTrue(entry.published_parsed is None)
        self.assertTrue('updated_parsed' in entry)
        self.assertTrue(entry.updated_parsed is None)
        data = self.feed.get_video_data(entry)
