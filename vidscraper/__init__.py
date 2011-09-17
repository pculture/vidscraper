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
from vidscraper import metasearch # MC uses 'vidscraper.metasearch'
from vidscraper.sites import (
    vimeo, google_video, youtube, blip, ustream, fora)

AUTOSCRAPE_SUITES = [
    vimeo.SUITE, google_video.SUITE, youtube.SUITE,
    blip.SUITE, ustream.SUITE, fora.SUITE]


def scrape_suite(url, suite, fields=None):
    """
    Scrapes a specified url using the recipe for the specified
    suite.  Returns a dict of data which can be constricted by the
    fields argument.

    :returns: dict of scraped data

    :raises errors.VideoDeleted: if the video no longer exists
    """
    scraped_data = {}

    funcs_map = suite['funcs']
    fields = fields or funcs_map.keys()
    order = suite.get('order')

    if order:
        # remove items in the order that are not in the fields
        order = order[:] # don't want to modify the one from the suite
        for field in set(order).difference(fields):
            order.remove(field)

        # add items that may have been missing from the order but
        # which are in the fields
        order.extend(set(fields).difference(order))
        fields = order

    shortmem = {}
    for field in fields:
        try:
            func = funcs_map[field]
        except KeyError:
            continue
        try:
            scraped_data[field] = func(url, shortmem=shortmem)
        except errors.VideoDeleted:
            raise
        except errors.Error:
            # ignore vidscraper errors
            pass

    return scraped_data


def is_scrapable(url):
    """Returns True if vidscraper can scrape this url, and False if
    it can't.
    """
    for suite in AUTOSCRAPE_SUITES:
        if suite['regex'].match(url):
            return True

    # If we get here that means that none of the regexes matched, so
    # we can't scrape it.
    return False

def auto_scrape(url, fields=None):
    """
    Automatically determines which suite to use and scrapes ``url`` with that
    suite.

    :returns: :class:`.ScrapedVideo` instance.

    :raises errors.CantIdentifyUrl: if this is not a url that can be
        scraped.
    """
    for suite in AUTOSCRAPE_SUITES:
        if suite['regex'].match(url):
            try:
                return scrape_suite(url, suite, fields)
            except IOError:
                raise errors.ParsingError(
                    "We failed to parse the page and got an IOError. " +
                    "Likely this is because the video was deleted, honestly.")

    # If we get here that means that none of the regexes matched, so
    # throw an error
    raise errors.CantIdentifyUrl(
        "No video scraping suite was found that can scrape that url")
