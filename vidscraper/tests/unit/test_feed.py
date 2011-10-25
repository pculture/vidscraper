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
import os
import unittest
import feedparser

from vidscraper.suites.feed import GenericFeedSuite

class GenericFeedSuiteTestCase(unittest.TestCase):
    def setUp(self):
        self.suite = GenericFeedSuite()
        self.old_SANITIZE = feedparser.SANITIZE_HTML
        feedparser.SANITIZE_HTML = False

    def tearDown(self):
        feedparser.SANITIZE_HTML = self.old_SANITIZE

    @property
    def data_file_dir(self):
        if not hasattr(self, '_data_file_dir'):
            test_dir = os.path.abspath(os.path.dirname(
                                                os.path.dirname(__file__)))
            self._data_file_dir = os.path.join(test_dir, 'data', 'feed')
        return self._data_file_dir

    # def test_CantIdentifyUrl_for_video(self):
    #     self.assertRaises(CantIdentifyUrl, self.suite.get_video,
    #                       'http://www.google.com/')

    def test_basic_feed_data(self):
        feed = self.suite.get_feed(
            'file://%s' % os.path.join(self.data_file_dir, 'feed.rss'))
        feed.load()
        self.assertEqual(feed.title, 'Internet Archive - Mediatype: movies')
        self.assertEqual(feed.webpage, 'http://www.archive.org/details/movies')
        self.assertEqual(
            feed.description,
            ('The most recent additions to the Internet Archive collections.  '
             'This RSS feed is generated dynamically'))
        self.assertEqual(feed.last_modified,
                         datetime.datetime(2011, 10, 20, 14, 36, 1))
        self.assertEqual(feed.entry_count, 2)
        
    def test_feed_entry_data(self):
        feed = self.suite.get_feed(
            'file://%s' % os.path.join(self.data_file_dir, 'feed.rss'))
        video = iter(feed).next()
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
            video.file_url,
            ("http://www.archive.org/download/"
             "SFGTV_20111020_130000/format=h.264"))
        self.assertEqual(video.file_url_mimetype, "video/h264")
        self.assertEqual(video.publish_datetime,
                         datetime.datetime(2011, 10, 20, 14, 14, 14))

    def test_feed_entry_unicode(self):
        feed = self.suite.get_feed(
            'file://%s' % os.path.join(self.data_file_dir, 'feed.rss'))
        i = iter(feed)
        i.next() # skip the first one
        video = i.next()
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
            video.file_url,
            ("http://www.archive.org/download/"
             "forsan2011-2196/format=h.264"))
        self.assertEqual(video.file_url_mimetype, "video/h264")
        self.assertEqual(video.publish_datetime,
                         datetime.datetime(2011, 10, 20, 14, 17, 44))
