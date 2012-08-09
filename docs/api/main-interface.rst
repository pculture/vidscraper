.. Copyright 2009 - Participatory Culture Foundation

   This file is part of vidscraper.

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions
   are met:

   1. Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
   2. Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.

   THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS`` AND ANY EXPRESS OR
   IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
   OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
   IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
   INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
   NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
   THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
   (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
   THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Main Interface
==============

The 5 functions given here should handle most use cases.

.. autofunction:: vidscraper.auto_scrape

.. autofunction:: vidscraper.auto_feed

.. autofunction:: vidscraper.auto_search

.. function:: vidscraper.handles_video

    Returns ``True`` if any registered suite can make a video with the
    given parameters, and ``False`` otherwise.

    .. note:: This does all the work of creating a video, then discards
              it. If you are going to use a video instance if one is
              created, it would be more efficient to use
              :func:`.auto_scrape` directly.

.. function:: vidscraper.handles_feed

    Returns ``True`` if any registered suite can make a feed with the
    given parameters, and ``False`` otherwise.

    .. note:: This does all the work of creating a feed, then discards
              it. If you are going to use a feed instance if one is
              created, it would be more efficient to use
              :func:`.auto_feed` directly.
