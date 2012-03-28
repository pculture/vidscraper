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

Most use cases will simply require the auto_scrape function.  Usage is
incredibly easy::

    >>> from vidscraper import auto_scrape
    >>> video = auto_scrape("http://www.youtube.com/watch?v=J_DV9b0x7v4")
    >>> video.title
    u'CaramellDansen (Full Version + Lyrics)'

That's it!  Couldn't be easier.  auto_scrape will determine the right
:doc:`scraping suite </api/suites>` to use for the url you pass in and will use that suite to return a :class:`.ScrapedVideo` instance that represents the data
associated with the video at that url. If no suites are found which support the
url, :exc:`.CantIdentifyUrl` will be raised.

If you only need certain fields (say you only need the "file_url" and the
"title" fields), you can pass those fields in as a second argument::

    >>> video = auto_scrape(url, fields=['file_url', 'title'])

Video fields
------------

If a :class:`.ScrapedVideo` is initialized without any fields, then
:mod:`vidscraper` will assume you want all of the fields for the video. When the
:class:`.ScrapedVideo` is being loaded, :mod:`vidscraper` will maximize the
number of requested fields that it fills; occasionally, this may mean that it
will make more than one HTTP request. This means that limiting the fields to
what you are actually using can save quite a bit of work.


Getting videos for a feed
+++++++++++++++++++++++++

If you want to get every video for a feed, you can use
:func:`vidscraper.auto_feed`::

    >>> from vidscraper import auto_feed
    >>> results = auto_feed("http://blip.tv/djangocon/rss")

This will read the feed at the given url and return a generator which yields :class:`.ScrapedVideo` instances for each entry in the feed. The instances will be preloaded with metadata from the feed. In many cases this will fill out all the fields that you need. If you need more, however, you can tell the video to load more data manually::

    >>> video = results.next()
    >>> video.load()

(Don't worry - if :mod:`vidscraper` can't figure out a way to get more data, it will simply do nothing!)

.. note:: Because this function returns a generator, the feed will actually be
          fetched the first time the generator's :meth:`next` method is called.

Crawling an entire feed
-----------------------

:func:`auto_feed` also supports feed crawling for some suites. You use it like this::

    >>> from vidscraper import auto_feed
    >>> results = auto_feed("http://blip.tv/djangocon/rss", crawl=True)

Now, when the generator runs out of results on the first page, it will
automatically fetch the next page, and then the next, and so on. This is not for
the faint of heart. Depending on the feed you're crawling, you could be there
for a while.

Searching video services
++++++++++++++++++++++++

It's also easy to run a search on a variety of services that support it. Simply do the following::

    >>> from vidscraper import auto_search
    >>> results = auto_search(['parrot'], exclude_terms=['dead']).values()

The search will be run on all suites that support searching, and the results will be returned as a dictionary mapping the suite used to the results for that feed.
