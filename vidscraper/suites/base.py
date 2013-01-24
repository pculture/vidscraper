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

import operator
import re

from vidscraper.exceptions import (UnhandledVideo, UnhandledFeed,
                                   UnhandledSearch)
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
        Registers a fallback suite, which is tried only if no other suite
        successfully handles a given video, feed, or search.

        """
        self._fallback = suite()

    def unregister(self, suite):
        """Unregisters a suite if it is registered."""
        if suite in self._suites:
            self._suites.remove(self._suite_dict[suite])
            del self._suite_dict[suite]

    def get_video(self, url, fields=None, api_keys=None, require_loaders=True):
        """
        For each registered :mod:`suite <vidscraper.suites>`, calls
        :meth:`~BaseSuite.get_video` with the given ``url``, ``fields``, and
        ``api_keys``, until a suite returns a :class:`.Video` instance.

        :param require_loaders: Changes the behavior if no suite is found
                                which handles the given parameters. If
                                ``True`` (default), :exc:`.UnhandledVideo`
                                will be raised; otherwise, a video will 
                                returned with the given ``url`` and
                                ``fields``, but it will not be able to load
                                any additional data.
        :raises: :exc:`.UnhandledVideo` if ``require_loaders`` is ``True`` and
                 no registered suite returns a video for the given parameters.
        :returns: :class:`.Video` instance with no data loaded.

        """
        for suite in self.suites:
            try:
                return suite.get_video(url, fields=fields, api_keys=api_keys)
            except UnhandledVideo:
                pass

        if require_loaders:
            raise UnhandledVideo(url)

        return Video(url, fields=fields)

    def get_feed(self, url, last_modified=None, etag=None, start_index=1,
                 max_results=None, video_fields=None, api_keys=None):
        """
        For each registered :mod:`suite <vidscraper.suites>`, calls
        :meth:`~BaseSuite.get_feed` with the given parameters, until a suite
        returns a feed instance.

        :returns: An instance of a specific suite's
                  :attr:`~.BaseSuite.feed_class` with no data loaded.

        :raises: :exc:`.UnhandledFeed` if no registered suites know how
                 to handle this url.

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
            except UnhandledFeed:
                pass
        raise UnhandledFeed(url)


    def get_searches(self, query, order_by='relevant', start_index=1,
                     max_results=None, video_fields=None, api_keys=None):
        """
        For each registered :mod:`suite <vidscraper.suites>`, calls
        :meth:`~.BaseSuite.get_search` with the given parameters.

        :returns: a list of iterators over search results for suites
                  which support the given parameters.

        """
        searches = []
        for suite in registry.suites:
            try:
                search = suite.get_search(query,
                                          order_by=order_by,
                                          start_index=start_index,
                                          max_results=max_results,
                                          video_fields=video_fields,
                                          api_keys=api_keys)
            except UnhandledSearch:
                pass
            else:
                searches.append(search)

        return searches

    def handles_video(self, *args, **kwargs):
        """
        Returns ``True`` if any registered suite can make a video with the
        given parameters, and ``False`` otherwise.

        .. note:: This does all the work of creating a video, then discards
                  it. If you are going to use a video instance if one is
                  created, it would be more efficient to use :meth:`get_video`
                  directly.

        """
        try:
            self.get_video(*args, **kwargs)
        except UnhandledVideo:
            return False
        return True

    def handles_feed(self, *args, **kwargs):
        """
        Returns ``True`` if any registered suite can make a feed with the
        given parameters, and ``False`` otherwise.

        .. note:: This does all the work of creating a feed, then discards
                  it. If you are going to use a feed instance if one is
                  created, it would be more efficient to use :meth:`get_feed`
                  directly.

        """
        try:
            self.get_feed(*args, **kwargs)
        except UnhandledFeed:
            return False
        return True


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

    #: A :class:`.BaseFeed` subclass that will be used to parse feeds for this
    #: suite.
    feed_class = None

    #: A :class:`.BaseSearch` subclass that will be used to run searches for
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
        return reduce(operator.or_, (l.fields for l in self.loader_classes))

    def get_video(self, url, fields=None, api_keys=None):
        """
        Returns a video using this suite's loaders. This instance will not
        have data loaded.

        :param url: A video URL. Video website URLs generally work; more
                    obscure urls (like API urls) might work as well.
        :param fields: A list of fields to be fetched for the video. Limiting this
                       may decrease the number of HTTP requests required for
                       loading the video.

                       .. seealso:: :ref:`video-fields`
        :param api_keys: A dictionary of API keys for various services. Check
                         the documentation for each
                         :mod:`suite <vidscraper.suites>` to find what API
                         keys they may want or require.
        :raises: :exc:`.UnhandledVideo` if none of this suite's loaders can
                 handle the given url and api keys.

        """
        # Sanity-check the url.
        if not url:
            raise UnhandledVideo(url)

        loaders = []

        for cls in self.loader_classes:
            try:
                loader = cls(url, api_keys=api_keys)
            except UnhandledVideo:
                continue

            loaders.append(loader)
        if not loaders:
            raise UnhandledVideo(url)
        return Video(url, loaders=loaders, fields=fields)

    def get_feed(self, url, *args, **kwargs):
        """
        Returns an instance of :attr:`feed_class`, which should be a subclass
        of :class:`.BaseFeed`.

        :raises: :exc:`.UnhandledFeed` if :attr:`feed_class` is None.

        """
        if self.feed_class is None:
            raise UnhandledFeed(url)
        return self.feed_class(url, *args, **kwargs)

    def get_search(self, *args, **kwargs):
        """
        Returns an instance of :attr:`search_class`, which should be a
        subclass of :class:`.BaseSearch`.

        :raises: :exc:`.UnhandledSearch` if :attr:`search_class` is None.

        """
        if self.search_class is None:
            raise UnhandledSearch(u"{0} does not support searches.".format(
                                  self.__class__.__name__))
        return self.search_class(*args, **kwargs)

    def handles_video(self, *args, **kwargs):
        """
        Returns ``True`` if this suite can make a video with the given
        parameters, and ``False`` otherwise.

        .. note:: This does all the work of creating a video, then discards
                  it. If you are going to use a video instance if one is
                  created, it would be more efficient to use :meth:`get_video`
                  directly.

        """
        try:
            self.get_video(*args, **kwargs)
        except UnhandledVideo:
            return False
        return True

    def handles_feed(self, *args, **kwargs):
        """
        Returns ``True`` if this suite can make a feed with the given
        parameters, and ``False`` otherwise.

        .. note:: This does all the work of creating a feed, then discards
                  it. If you are going to use a feed instance if one is
                  created, it would be more efficient to use :meth:`get_feed`
                  directly.

        """
        try:
            self.get_feed(*args, **kwargs)
        except UnhandledFeed:
            return False
        return True

    def handles_search(self, *args, **kwargs):
        """
        Returns ``True`` if this suite can make a search with the given
        parameters, and ``False`` otherwise.

        .. note:: This does all the work of creating a search, then discards
                  it. If you are going to use a search instance if one is
                  created, it would be more efficient to use
                  :meth:`get_search` directly.

        """
        try:
            self.get_search(*args, **kwargs)
        except UnhandledSearch:
            return False
        return True
