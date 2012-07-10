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

Vidscraper is a clean, simple library for a couple of rather messy
issues:

- Retrieving the source video from a "flash-only" website
- Finding out contextual data about a pasted url: title/description/etc

Vidscraper provides a unified api for an issue that requires a lot of
one-off scraping.


Requirements
++++++++++++

* Python 2.6+
* BeautifulSoup 4.0.2
* feedparser 5.1.2+
* lxml 2.3.4+
* python-requests 0.13.0+

Optional
--------
* requests-oauth 0.4.1+ (for some APIs *\*cough\* Vimeo searching \*cough\** which require authentication)
* unittest2 (for tests)
* mock (for tests)


Contents
++++++++

.. toctree::
   :maxdepth: 2

   topics/getting-started
   exceptions
   api/suites
   api/videos

Release notes
+++++++++++++

.. toctree::
   :maxdepth: 1

   release-notes/0.6

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

