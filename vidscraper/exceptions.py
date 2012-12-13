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


class VidscraperError(Exception):
    """Base error for :mod:`vidscraper`."""
    pass


class UnhandledVideo(VidscraperError):
    """
    Raised by :class:`.VideoLoader`\ s and :doc:`suites </api/suites>` if a
    given video can't be handled.

    """
    pass


class UnhandledFeed(VidscraperError):
    """
    Raised if a feed can't be handled by a :doc:`suite </api/suites>` or
    :class:`.BaseFeed` subclass.

    """
    pass


class UnhandledSearch(VidscraperError):
    """
    Raised if a search can't be handled by a :doc:`suite </api/suites>` or
    :class:`.BaseSearch` subclass.

    """
    pass


class InvalidVideo(VidscraperError):
    """
    Raised if a video is found to be invalid in some way after data has
    been collected on it.

    """
    pass


class VideoDeleted(VidscraperError):
    """Raised if the remote server has deleted the video being scraped."""
    pass
