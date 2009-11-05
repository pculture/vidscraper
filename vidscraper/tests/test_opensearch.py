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

import feedparser
import unittest

from vidscraper.bulk_import import opensearch

SMALL_FEED = 'http://www.youtube.com/rss/user/macedky/videos.rss'
BIG_FEED = 'http://www.youtube.com/rss/user/DragonOpenVideo/videos.rss'

SMALL_FEED_PARSED = feedparser.parse(SMALL_FEED)
BIG_FEED_PARSED = feedparser.parse(BIG_FEED)
class OpenSearchBulkImportTestCase(unittest.TestCase):

    def test_video_count(self):
        """
        video_count(parsed_feed) should return the number of total videos in
        the OpenSearch-enabled feed.  If the feed is not an OpenSearch feed,
        return None.
        """
        self.assertEquals(opensearch.video_count(SMALL_FEED_PARSED), 1)
        self.assert_(58 <= opensearch.video_count(BIG_FEED_PARSED) <= 62,
                     opensearch.video_count(BIG_FEED_PARSED))
        self.assertEquals(opensearch.video_count(
                feedparser.parse('http://miropcf.blip.tv/rss')), None)

    def test_bulk_import_big(self):
        """
        bulk_import(parsed_feed) should return a FeedParserDict which contains
        all the entries from the feed.
        """
        feed = opensearch.bulk_import(BIG_FEED_PARSED)
        self.assertEquals(len(feed.entries), 58)
        self.assertEquals(feed.entries[0].title, '00270')
        self.assertEquals(feed.entries[-1].title, '00124')

    def test_bulk_import_small(self):
        """
        bulk_import(parsed_feed) should return a FeedParserDict which contains
        all the entries from the feed, even if the feed does not span multiple
        pages.
        """
        feed = opensearch.bulk_import(SMALL_FEED_PARSED)
        self.assertEquals(len(feed.entries), 1)
        self.assertEquals(feed.entries[0].title,
                          'SE Telephone Lg Video')
