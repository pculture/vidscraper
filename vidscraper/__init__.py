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

__version__ = (1, 0, 2)


from vidscraper.suites import registry


def auto_scrape(url, fields=None, api_keys=None):
    """
    Returns a :class:`.Video` instance with data loaded.

    :param url: A video URL. Video website URLs generally work; more
                obscure urls (like API urls) might work as well.
    :param fields: A list of fields to be fetched for the video. Limiting this
                   may decrease the number of HTTP requests required for
                   loading the video.

                   .. seealso:: :ref:`video-fields`
    :param api_keys: A dictionary of API keys for various services. Check the
                     documentation for each :mod:`suite <vidscraper.suites>`
                     to find what API keys they may want or require.
    :raises: :exc:`.UnhandledVideo` if no :mod:`suite <vidscraper.suites>`
             can be found which handles the video.

    """
    video = registry.get_video(url, fields=fields, api_keys=api_keys)
    video.load()
    return video


auto_feed = registry.get_feed
auto_search = registry.get_searches
handles_video = registry.handles_video
handles_feed = registry.handles_feed
