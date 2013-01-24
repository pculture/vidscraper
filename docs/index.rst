.. Vidscraper documentation master file, created by
   sphinx-quickstart on Thu Sep 15 21:08:41 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

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

.. module:: vidscraper

Welcome to Vidscraper's documentation!
======================================

Vidscraper is a library for retrieving information about videos from
various sources – video feeds, APIs, page scrapes – combining it, and
presenting it in a unified manner, all as efficiently as possible.

Vidscraper comes with built-in support for popular video sites like
blip_, vimeo_, ustream_, and youtube_, as well support for generic RSS
feeds with feedparser_.

.. _blip: http://blip.tv
.. _vimeo: http://vimeo.com
.. _ustream: http://ustream.tv
.. _youtube: http://youtube.com

Quick example
=============

::

    >>> import vidscraper
    >>> video = vidscraper.auto_scrape('http://www.youtube.com/watch?v=PMpu8jH1LE8') 
    >>> video.title
    u"The Magic Roundabout - Ermintrude's Folly"
    >>> video.description
    u"Ermintrude's been at the poppies again, but it's Dougal who ends up high as a kite!"
    >>> video.user
    u'nickhirst999'
    >>> video.guid
    'http://gdata.youtube.com/feeds/api/videos/PMpu8jH1LE8'


Command line
++++++++++++

vidscraper also comes with a command line utility allowing you to get
video metadata from the command line. The example above could look like
this:

.. code-block:: bash

    $ vidscraper video http://www.youtube.com/watch?v=PMpu8jH1LE8 \
      --fields=title,description,user,guid
    Scraping http://www.youtube.com/watch?v=PMpu8jH1LE8...
    {
      "description": "Ermintrude's been at the poppies again, but it's Dougal who ends up high as a kite!", 
      "fields": [
        "title", 
        "description", 
        "user", 
        "guid"
      ], 
      "guid": "http://gdata.youtube.com/feeds/api/videos/PMpu8jH1LE8", 
      "title": "The Magic Roundabout - Ermintrude's Folly", 
      "url": "http://www.youtube.com/watch?v=PMpu8jH1LE8", 
      "user": "nickhirst999"
    }


Project links
=============

:code:         https://github.com/pculture/vidscraper/
:docs:         http://vidscraper.readthedocs.org/
:bugtracker:   http://bugzilla.pculture.org/
:code:         https://github.com/pculture/vidscraper/
:irc:          `#vidscraper on irc.freenode.net <irc://irc.freenode.net/vidscraper>`_
:build status: |build-image|

.. |build-image| image:: https://secure.travis-ci.org/pculture/vidscraper.png?branch=develop
                 :target: http://travis-ci.org/pculture/vidscraper/builds


Requirements
++++++++++++

* Python_ 2.6+
* BeautifulSoup_ 4.0.2+
* feedparser_ 5.1.2+
* `python-requests`_ 0.13.0+ (But less than 1.0.0!)

.. _Python: http://www.python.org/
.. _BeautifulSoup: http://www.crummy.com/software/BeautifulSoup/
.. _feedparser: http://code.google.com/p/feedparser/
.. _`python-requests`: http://python-requests.org/

Optional
--------
* `requests-oauth`_ 0.4.1+ (for some APIs *\*cough\* Vimeo searching \*cough\** which require authentication)
* lxml_ 2.3.4+ (recommended for BeautifulSoup; assumed parser for test results.)
* unittest2_ 0.5.1+ (for tests)
* mock_ 0.8.0+ (for tests)
* tox_ 1.4.2+ (for tests)

.. _`requests-oauth`: https://github.com/maraujop/requests-oauth
.. _lxml: http://lxml.de/
.. _unittest2: http://pypi.python.org/pypi/unittest2/
.. _mock: http://www.voidspace.org.uk/python/mock/
.. _tox: http://tox.readthedocs.org/


User Guide
++++++++++

.. toctree::
   :maxdepth: 2

   guide/getting-started

API Documentation
+++++++++++++++++

.. toctree::
   :maxdepth: 2

   api/main-interface
   api/exceptions
   api/suites
   api/videos

Release notes
+++++++++++++

.. toctree::
   :maxdepth: 1

   release-notes/1.0.2
   release-notes/1.0.1
   release-notes/1.0.0

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

