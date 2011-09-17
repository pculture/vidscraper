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

	from vidscraper import auto_scrape
	video = auto_scrape(my_url)

That's it!  Couldn't be easier.  auto_scrape will determine the right
:doc:`scraping suite </api/suites>` to use for ``my_url`` and will use that
suite to return a :class:`.ScrapedVideo` instance that represents the data
associated with the video at that url. If no suites are found which support the
url, :exc:`.CantIdentifyUrl` will be raised.

If you only need certain fields (say you only need the "file_url" and the
"title" fields), you can potentially save some unnecessary work by passing
in a list of fields as a second argument::

	video = auto_scrape(url, fields=['file_url', 'title'])

In some cases, this may even reduce the number of HTTP requests required.
