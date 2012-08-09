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

Getting Started
===============

Scraping video pages
++++++++++++++++++++

Most use cases will simply require the :func:`.auto_scrape` function.

::

    >>> from vidscraper import auto_scrape
    >>> video = auto_scrape("http://www.youtube.com/watch?v=J_DV9b0x7v4")
    >>> video.title
    u'CaramellDansen (Full Version + Lyrics)'

That's it! Couldn't be easier. :func:`.auto_scrape` will pull down
metadata from all the places it can figure out based on the url you
entered and return a :class:`.Video` instance loaded with that data.

If :mod:`vidscraper` doesn't know how to fetch data for that url – for
example, if you try to scrape google.com (which isn't a video page) –
:exc:`.UnhandledVideo` will be raised.

.. _video-fields:

Limiting metadata
-----------------

Videos can have metadata pulled from a number of sources - for
example, a page scrape, an OEmbed API, and a service-specific API.
When loading video data, :mod:`vidscraper` will query as many of these
services as it needs to provide the data you ask for.

So, if you only need certain pieces of metadata (say the title and
description of a video), you can pass those fields to
:func:`.auto_scrape` and potentially save HTTP requests::

    >>> video = auto_scrape(url, fields=['title', 'description'])

.. seealso:: :class:`.Video`


Getting videos for a feed
+++++++++++++++++++++++++

If you want to get every video for a feed, you can use
:func:`.auto_feed`::

    >>> from vidscraper import auto_feed
    >>> feed = auto_feed("http://blip.tv/djangocon/rss")

This will read the feed at the given url and return a generator which
yields :class:`.Video` instances for each entry in the feed. The
instances will be preloaded with metadata from the feed. In many cases
this will fill out all the fields that you need. If you need more,
however, you can tell the video to load more data manually::

    >>> video = feed.next()
    >>> video.load()

(Don't worry - if :mod:`vidscraper` can't figure out a way to get more
data, it will simply do nothing!)

The feed instance is a lazy generator - it won't make any HTTP
requests until you call :meth:`~.VideoIterator.next` the first time.
It will only make a second request once you've gotten to the bottom of
the first page.

Not crawling a whole feed
-------------------------

By default, :func:`.auto_feed` will try to crawl through the entire
feed. Depending on the feed you're crawling, you could be there for a
while. If you're pressed for time (or bandwidth) you can limit the
number of videos you pull down::

    >>> from vidscraper import auto_feed
    >>> feed = auto_feed("http://blip.tv/djangocon/rss")
    >>> len(list(feed))
    117
    >>> feed = auto_feed("http://blip.tv/djangocon/rss", max_results=20)
    >>> len(list(feed))
    20

Searching video services
++++++++++++++++++++++++

It's also easy to run a search on a variety of services with
:func:`.auto_search`::

    >>> from vidscraper import auto_search
    >>> searches = auto_search('parrot -dead', max_results=20)
    >>> searches
    [<vidscraper.suites.blip.Search object at 0x10b490f90>,
     <vidscraper.suites.youtube.Search object at 0x10b49f090>]

You'll get back a list of search iterables for suites which support
the search parameters. These have the same behavior in terms of
loading new pages that you see in the feed iterator.

::

    >>> video = searches[0].next()
    >>> video.title
    u"Episode 57: iMovie HD '06, Part II"
