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

import itertools
import json
import operator
import re
import urllib
import urllib2

import feedparser
import requests
try:
    from requests import async
except RuntimeError:
    async = None

from vidscraper.exceptions import UnhandledURL, UnhandledSearch
from vidscraper.utils.feedparser import (struct_time_to_datetime,
                                         get_item_thumbnail_url)
from vidscraper.videos import Video


RegexpPattern = type(re.compile(''))


class SuiteRegistry(object):
    """
    A registry of suites. Suites may be registered, unregistered, and iterated
    over.

    """

    def __init__(self):
        self._suites = []
        self._suite_dict = {}
        self._fallback = None

    @property
    def suites(self):
        """
        Returns a tuple of registered suites. If a fallback is registered, it
        will always be at the end of this tuple.

        """
        suites = tuple(self._suites)
        if self._fallback is not None:
            suites += (self._fallback,)
        return suites

    def register(self, suite):
        """Registers a suite if it is not already registered."""
        if suite not in self._suite_dict:
            self._suite_dict[suite] = suite()
            self._suites.append(self._suite_dict[suite])

    def register_fallback(self, suite):
        """
        Registers a fallback suite, which used only if no other suite
        succeeds. If no fallback is registered, then :exc:`.UnhandledURL` will
        be raised for unknown videos/feeds.

        """
        self._fallback = suite()

    def unregister(self, suite):
        """Unregisters a suite if it is registered."""
        if suite in self._suites:
            self._suites.remove(self._suite_dict[suite])
            del self._suite_dict[suite]

    def get_video(self, url, fields=None, api_keys=None, require_loaders=True):
        """
        Automatically determines which suite to use and scrapes ``url`` with
        that suite. The parameters ``url``, ``fields``, and ``api_keys`` have
        the same meaning as for :class:`.Video`.

        :param require_loaders: If ``True``, a video will only be returned if
                                a suite is found which can provide loaders.
                                If ``False`` and no suite is found, a video
                                with no loaders will be returned.
        :type require_loaders: boolean
        :returns: :class:`.Video` instance.

        :raises UnhandledURL: If ``require_suite`` is ``True`` and no
                              registered suite knows how to handle the url.

        """
        for suite in self.suites:
            try:
                return suite.get_video(url, fields=fields, api_keys=api_keys)
            except UnhandledURL:
                pass

        if require_loaders:
            raise UnhandledURL(url)

        return Video(url, fields=fields, api_keys=api_keys)

    def get_feed(self, url, last_modified=None, etag=None, start_index=1,
                 max_results=None, video_fields=None, api_keys=None):
        """
        Tries to get a :class:`.VideoFeed` instance from each suite in sequence.
        The parameters are the same as those for :class:`.VideoFeed`.

        :returns: A :class:`VideoFeed` instance which yields
                  :class:`.Video` instances for the items in the feed.

        :raises UnhandledURL: if no registered suites know how to handle this url.

        """
        for suite in self.suites:
            try:
                return suite.get_feed(url,
                                      last_modified=last_modified,
                                      etag=etag,
                                      start_index=start_index,
                                      max_results=max_results,
                                      video_fields=video_fields,
                                      api_keys=api_keys)
            except UnhandledURL:
                pass
        raise UnhandledURL(url)


    def get_searches(self, query, order_by='relevant', start_index=1,
                     max_results=None, video_fields=None, api_keys=None):
        """
        Returns a dictionary mapping each registered suite to a
        :class:`.VideoSearch` instance which has been instantiated for that suite
        and the given arguments.

        """
        searches = {}
        for suite in registry.suites:
            try:
                searches[suite] = suite.get_search(query,
                                                   order_by=order_by,
                                                   start_index=start_index,
                                                   max_results=max_results,
                                                   video_fields=video_fields,
                                                   api_keys=api_keys)
            except UnhandledSearch:
                pass

        return searches


#: An instance of :class:`.SuiteRegistry` which is used by :mod:`vidscraper` to
#: track registered suites.
registry = SuiteRegistry()


class BaseSuite(object):
    """
    This is a base class for suites, demonstrating the API which is expected
    when interacting with suites. It is not suitable for actual use; some vital
    methods must be defined on a suite-by-suite basis.

    """
    #: A string or precompiled regular expression which will be matched against
    #: video urls to check if they can be handled by this suite.
    video_regex = None

    #: A string or precompiled regular expression which will be matched against
    #: feed urls to check if they can be handled by this suite.
    feed_regex = None

    #: A list or tuple of :class:`.VideoLoader` classes which will be used to
    #: populate videos with data. These loaders will be run in the order they
    #: are given, so it's a good idea to order them by the effort they would
    #: require; for example, OEmbed should generally come first, since the
    #: response is small and easy to parse compared to, say, a page scrape.
    #:
    #: .. seealso:: :meth:`.Video.run_loaders`
    loader_classes = ()

    #: A :class:`VideoFeed` subclass that will be used to parse feeds for this
    #: suite.
    feed_class = None

    #: A :class:`VideoFeed` subclass that will be used to run searches for
    #: this suite.
    search_class = None

    def __init__(self):
        if isinstance(self.video_regex, basestring):
            self.video_regex = re.compile(self.video_regex)
        if isinstance(self.feed_regex, basestring):
            self.feed_regex = re.compile(self.feed_regex)

    def __getstate__(self):
        state = self.__dict__.copy()
        regexes = {}
        for key, value in state.items():
            if isinstance(value, RegexpPattern):
                regexes[key] = value.pattern
        state['_regexes'] = regexes
        for key in regexes:
            del state[key]
        return state

    def __setstate__(self, state):
        regexes = state.pop('_regexes')
        for key, value in regexes.items():
            state[key] = re.compile(value)
        self.__dict__ = state

    @property
    def available_fields(self):
        """
        Returns a set of all of the fields we could possibly get from this
        suite.
        """
        return reduce(operator.or_, (m.fields for m in self.methods))

    def handles_video_url(self, url):
        """
        Returns ``True`` if this suite can handle the ``url`` as a video and
        ``False`` otherwise. By default, this method will check whether the url
        matches :attr:`.video_regex` or raise a :exc:`NotImplementedError` if
        that is not possible.

        """
        try:
            self.get_video(url)
        except UnhandledURL:
            return False
        return True

    def handles_feed_url(self, url):
        """
        Returns ``True`` if this suite can handle the ``url`` as a feed and
        ``False`` otherwise.

        """
        try:
            self.get_feed(url)
        except UnhandledURL:
            return False
        return True

    def get_video(self, url, fields=None, api_keys=None):
        """
        Returns a video using this suite's loaders.

        :raises UnhandledURL: if none of this suite's loaders can handle the
                              given url and api keys.

        """
        loaders = []

        for cls in self.loader_classes:
            try:
                loader = cls(url, api_keys=api_keys)
            except UnhandledURL:
                continue

            loaders.append(loader)
        if not loaders:
            raise UnhandledURL(url)
        return Video(url, self, *args, **kwargs)

    def get_feed(self, url, *args, **kwargs):
        """Returns an instance of :attr:`feed_class`."""
        if self.feed_class is None:
            raise UnhandledURL(url)
        return self.feed_class(url, *args, **kwargs)

    def get_search(self, *args, **kwargs):
        """Returns an instance of :attr:`search_class`."""
        if self.search_class is None:
            raise UnhandledSearch(u"{0} does not support searches.".format(
                                  self.__class__.__name__))
        return self.search_class(*args, **kwargs)
