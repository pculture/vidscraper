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
from vidscraper.videos import Video, VideoFeed, VideoSearch


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
        """Returns a tuple of registered suites."""
        return tuple(self._suites)

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

    def suite_for_video_url(self, url):
        """
        Returns the first registered suite which can handle the ``url`` as a
        video or raises :exc:`.UnhandledURL` if no such suite is found.

        """
        for suite in self._suites:
            try:
                if suite.handles_video_url(url):
                    return suite
            except NotImplementedError:
                pass
        if self._fallback and self._fallback.handles_video_url(url):
            return self._fallback
        raise UnhandledURL

    def suite_for_feed_url(self, url):
        """
        Returns the first registered suite which can handle the ``url`` as a
        feed or raises :exc:`.UnhandledURL` if no such suite is found.

        """
        for suite in self._suites:
            try:
                if suite.handles_feed_url(url):
                    return suite
            except NotImplementedError:
                pass
        if self._fallback and self._fallback.handles_feed_url(url):
            return self._fallback
        raise UnhandledURL


#: An instance of :class:`.SuiteRegistry` which is used by :mod:`vidscraper` to
#: track registered suites.
registry = SuiteRegistry()


class SuiteMethod(object):
    """
    This is a base class for suite data-fetching methods (for example, oembed,
    API, or scraping). Currently, all of the base functionality should be
    overridden; however, this class should still be subclassed in case shared
    functionality is added later.

    """
    #: A set of fields provided by this method.
    fields = set()

    def get_url(self, video):
        """
        Returns the url to fetch for this method. Must be implemented by
        subclasses.

        """
        raise NotImplementedError

    def process(self, response):
        """
        Parse the :mod:`requests` response into a dictionary mapping
        :class:`.Video` field names to values. Must be implemented by
        subclasses.

        """
        raise NotImplementedError


class OEmbedMethod(SuiteMethod):
    """
    Basic OEmbed support for any suite.

    :param endpoint: The endpoint url for this suite's oembed API.

    """
    fields = set(['title', 'user', 'user_url', 'thumbnail_url', 'embed_code'])

    def __init__(self, endpoint):
        self.endpoint = endpoint

    def get_url(self, video):
        return u"%s?url=%s" % (self.endpoint, urllib.quote_plus(video.url))

    def process(self, response):
        parsed = json.loads(response.text)
        data = {
            'title': parsed['title'],
            'user': parsed['author_name'],
            'user_url': parsed['author_url'],
            'thumbnail_url': parsed['thumbnail_url'],
            'embed_code': parsed['html']
        }
        return data


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

    #: A list or tuple of :class:`SuiteMethod` instances which will be used to
    #: populate videos with data. These methods will be attempted in the order
    #: they are given, so it's a good idea to order them by the effort they
    #: require; for example, OEmbed should generally come first, since the
    #: response is small and easy to parse compared to, say, a page scrape.
    #:
    #: .. seealso:: :meth:`BaseSuite.run_methods`
    methods = ()

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
        if self.video_regex is None:
            return False
        return bool(self.video_regex.match(url))

    def handles_feed_url(self, url):
        """
        Returns ``True`` if this suite can handle the ``url`` as a feed and
        ``False`` otherwise.

        """
        if self.feed_class is None:
            return False
        try:
            self.feed_class(url)
        except UnhandledURL:
            return False
        return True

    def get_video(self, url, **kwargs):
        """Returns a video using this suite."""
        return Video(url, self, **kwargs)

    def get_feed(self, *args, **kwargs):
        """Returns an instance of :attr:`feed_class`."""
        if self.feed_class is None:
            raise UnhandledURL
        return self.feed_class(*args, **kwargs)

    def get_search(self, *args, **kwargs):
        """Returns an instance of :attr:`search_class`."""
        if self.search_class is None:
            raise UnhandledSearch
        return self.search_class(*args, **kwargs)

    def find_best_methods(self, missing_fields):
        """
        Generates a dictionary where the keys are numbers of remaining fields
        and the values are combinations of methods that promise to yield that
        number of remaining fields, in the order that they are encountered.

        """
        # Our initial state is that we cover none of the missing fields, and
        # that we use none of the available methods.
        min_remaining = len(missing_fields)
        best_methods = []

        # Loop through all combinations of any size that can be made with the
        # available methods.
        for size in xrange(1, len(self.methods) + 1):
            for methods in itertools.combinations(self.methods, size):
                # First, build a set of the fields that are provided by the
                # methods.
                field_set = reduce(operator.or_, (m.fields for m in methods))
                remaining = len(missing_fields - field_set)

                # If these methods fill all the missing fields, take them
                # immediately.
                if not remaining:
                    return methods

                # Otherwise, note the methods iff they would decrease the 
                # number of missing fields.
                if remaining < min_remaining:
                    best_methods = methods
                    min_remaining = remaining
        return best_methods


    def run_methods(self, video):
        """
        Selects methods from :attr:`methods` which can be used in combination
        to fill all missing fields on the ``video`` - or as many of them as
        possible.

        This will prefer the first listed methods and will prefer small
        combinations of methods, so that the smallest number of smallest
        possible responses will be fetched.

        """
        missing_fields = set(video.missing_fields)
        if not missing_fields:
            return

        best_methods = self.find_best_methods(missing_fields)

        if async is None:
            responses = [requests.get(m.get_url(video), timeout=3)
                         for m in best_methods]
        else:
            responses = async.map([async.get(m.get_url(video), timeout=3)
                                   for m in best_methods])

        data = {}
        for method, response in itertools.izip(best_methods, responses):
            data.update(method.process(response))

        return data
