# Miro - an RSS based video player application
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

from vidscraper import errors
from vidscraper.suites import ScrapedVideo, registry, ScrapedSearch, ScrapedFeed


VERSION = '0.5.0a'


def handles_video_url(url):
    """
    Returns True if vidscraper can scrape this url, and False if
    it can't.

    """
    return any((suite.handles_video_url(url) for suite in registry.suites))


def handles_feed_url(url):
    """
    Returns True if vidscraper can treat this url as a feed, and False if
    it can't.

    """
    return any((suite.handles_feed_url(url) for suite in registry.suites))


def auto_scrape(url, fields=None):
    """
    Automatically determines which suite to use and scrapes ``url`` with that
    suite.

    :returns: :class:`.ScrapedVideo` instance.

    :raises errors.CantIdentifyUrl: if this is not a url that can be
        scraped.

    """
    video = ScrapedVideo(url, fields=fields)
    video.load()
    return video


def auto_feed(feed_url, fields=None, crawl=False):
    """
    Automatically determines which suite to use and scrapes ``feed_url`` with
    that suite. This will return a generator of :class:`.ScrapedVideo` instances
    which have been initialized with the given ``fields``. If ``crawl`` is
    ``True`` (not the default) then :mod:`vidscraper` will return results from
    multiple pages of the feed, if the suite supports it.

    .. note:: Crawling will only initiate a new HTTP request after it has
              exhausted the results on the current page.

    :returns: A generator which yields :class:`.ScrapedVideo` instances for the
              items in the feed.

    :raises errors.CantIdentifyUrl: if this is a url which none of the suites
                                    know how to handle.

    """
    for suite in registry.suites:
        if suite.handles_feed_url(feed_url):
            return suite.get_feed(feed_url, fields, crawl)
    raise errors.CantIdentifyUrl


def auto_search(query, fields=None, order_by=None, crawl=False,
                max_results=None, api_keys=None):
    """
    Returns a discionary mapping each registered suite to a
    :class:`.ScrapedSearch` instance which has been instantiated for that suite
    and the given arguments.

    """
    suites = {}
    for suite in registry.suites:
        suites[suite] = ScrapedSearch(suite, query, fields, order_by, crawl,
                                      max_results, api_keys)
    return suites
