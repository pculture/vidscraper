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

from vidscraper.errors import CantIdentifyUrl
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
        """Registers a fallback suite, which used only if no other suite
        succeeds.  If no fallback is registered, then CantIdentifyUrl will be
        raised for unknown videos/feeds.
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
        video or raises :exc:`.CantIdentifyUrl` if no such suite is found.

        """
        for suite in self._suites:
            try:
                if suite.handles_video_url(url):
                    return suite
            except NotImplementedError:
                pass
        if self._fallback and self._fallback.handles_video_url(url):
            return self._fallback
        raise CantIdentifyUrl

    def suite_for_feed_url(self, url):
        """
        Returns the first registered suite which can handle the ``url`` as a
        feed or raises :exc:`.CantIdentifyUrl` if no such suite is found.

        """
        for suite in self._suites:
            try:
                if suite.handles_feed_url(url):
                    return suite
            except NotImplementedError:
                pass
        if self._fallback and self._fallback.handles_feed_url(url):
            return self._fallback
        raise CantIdentifyUrl


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
        :class:`Video` field names to values. Must be implemented by
        subclasses.

        """
        raise NotImplementedError


class OEmbedMethod(SuiteMethod):
    fields = set(['title', 'user', 'user_url', 'thumbnail_url', 'embed_code'])

    def __init__(self, endpoint):
        """Takes an ``endpoint`` - a URL for an oembed API."""
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
            return bool(self.video_regex.match(url))
        except AttributeError:
            raise NotImplementedError

    def handles_feed_url(self, url):
        """
        Returns ``True`` if this suite can handle the ``url`` as a feed and
        ``False`` otherwise. By default, this method will check whether the url
        matches :attr:`.feed_regex` or raise a :exc:`NotImplementedError` if
        that is not possible.

        """
        try:
            return bool(self.feed_regex.match(url))
        except AttributeError:
            raise NotImplementedError

    def get_feed_url(self, url):
        """
        Some suites can handle URLs that are not technically feeds, but can
        convert them into a feed that is usable.  This method can be overidden
        to do that conversion.  By default, this method just returns the
        original URL.

        """
        return url

    def get_feed(self, url, **kwargs):
        """Returns a feed using this suite."""
        return VideoFeed(url, self, **kwargs)

    def get_video(self, url, **kwargs):
        """Returns a video using this suite."""
        return Video(url, self, **kwargs)

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

    def get_feed_response(self, feed, feed_url):
        """
        Returns a parsed response for this ``feed``. By default, this uses
        :mod:`feedparser` to get a response for the ``feed_url`` and returns
        the resulting structure.

        """
        response = feedparser.parse(feed_url)
        # Don't let feedparser silence connection problems.
        if isinstance(response.get('bozo_exception', None), urllib2.URLError):
            raise response.bozo_exception
        return response

    def get_feed_info_response(self, feed, response):
        """
        In case the response for the given ``feed`` needs to do other work on
        ``reponse`` to get feed information (title, &c), suites can override
        this method to do that work.  By default, this method just returns the
        ``response`` it was given.
        """
        return response

    def get_feed_title(self, feed, feed_response):
        """
        Returns a title for the feed based on the ``feed_response``, or
        ``None`` if no title can be determined. By default, assumes that the
        response is a :mod:`feedparser` structure and returns a value based on
        that.

        """
        return feed_response.feed.get('title')

    def get_feed_entry_count(self, feed, feed_response):
        """
        Returns an estimate of the total number of entries in this feed, or
        ``None`` if that cannot be determined. By default, returns the number
        of entries in the feed.

        """
        return len(feed_response.entries)

    def get_feed_description(self, feed, feed_response):
        """
        Returns a description of the feed based on the ``feed_response``, or
        ``None`` if no description can be determined. By default, assumes that
        the response is a :mod:`feedparser` structure and returns a value based
        on that.

        """
        return feed_response.feed.get('subtitle')

    def get_feed_webpage(self, feed, feed_response):
        """
        Returns the url for an HTML version of the ``feed_response``, or
        ``None`` if no such url can be determined. By default, assumes that
        the response is a :mod:`feedparser` structure and returns a value based
        on that.

        """
        return feed_response.feed.get('link')

    def get_feed_guid(self, feed, feed_response):
        """
        Returns the guid of the ``feed_response``, or ``None`` if no guid can
        be determined. By default, assumes that the response is a
        :mod:`feedparser` structure and returns a value based on that.

        """
        return feed_response.feed.get('id')

    def get_feed_thumbnail_url(self, feed, feed_response):
        """
        Returns the thumbnail URL of the ``feed_response``, or ``None`` if no
        thumbnail can be found.  By default, assumes that the response is a
        :mod:`feedparser` structur4e and returns a value based on that.
        """
        try:
            return get_item_thumbnail_url(feed_response.feed)
        except KeyError:
            return None

    def get_feed_last_modified(self, feed, feed_response):
        """
        Returns the last modification date for the ``feed_response`` as a
        python datetime, or ``None`` if no date can be determined. By default,
        assumes that the response is a :mod:`feedparser` structure and returns
        a value based on that.

        """
        struct_time = feed_response.feed.get('updated_parsed')
        return (struct_time_to_datetime(struct_time)
                if struct_time is not None else None)

    def get_feed_etag(self, feed, feed_response):
        """
        Returns the etag for a ``feed_response``, or ``None`` if no such url
        can be determined. By default, assumes that the response is a
        :mod:`feedparser` structure and returns a value based on that.

        """
        return feed_response.feed.get('etag')

    def get_feed_entries(self, feed, feed_response):
        """
        Returns an iterable of feed entries for a ``feed_response`` as returned
        from :meth:`get_feed_response`. By default, this assumes that the
        response is a :mod:`feedparser` structure and tries to return its
        entries.

        """
        return feed_response.entries

    def parse_feed_entry(self, entry):
        """
        Given a feed entry (as returned by :meth:`.get_feed_entries`), creates
        and returns a dictionary containing data from the feed entry, suitable
        for application via :meth:`apply_video_data`. Must be implemented by
        subclasses.

        """
        raise NotImplementedError

    def get_next_feed_page_url(self, feed, feed_response):
        """
        Based on a ``feed_response`` and a :class:`VideoFeed` instance,
        generates and returns a url for the next page of the feed, or returns
        ``None`` if that is not possible. By default, simply returns ``None``.
        Subclasses must override this method to have a meaningful feed crawl.

        """
        return None

    def get_search_url(self, search):
        """
        Returns a url which this suite can use to fetch search results for the
        given string. Must be implemented by subclasses.

        """
        raise NotImplementedError

    def get_search(self, query, **kwargs):
        """
        Returns a search using this suite.
        """
        return VideoSearch(query, self, **kwargs)

    def get_search_response(self, search, search_url):
        """
        Returns a parsed response for the given ``search_url``. By default,
        assumes that the url references a feed and passes the work off to
        :meth:`.get_feed_response`.

        """
        return self.get_feed_response(search, search_url)

    def get_search_total_results(self, search, search_response):
        """
        Returns an estimate for the total number of search results based on the
        first response returned by :meth:`get_search_response` for the
        :class:`VideoSearch`. By default, assumes that the url references a
        feed and passes the work off to :meth:`.get_feed_entry_count`.
        """
        return self.get_feed_entry_count(search, search_response)

    def get_search_time(self, search, search_response):
        """
        Returns the amount of time required by the service provider for the
        suite to execute the search. By default, simply returns ``None``.

        """
        return None

    def get_search_results(self, search, search_response):
        """
        Returns an iterable of search results for a :class:`VideoSearch` and
        a ``search_response`` as returned by :meth:`.get_search_response`. By
        default, assumes that the ``search_response`` is a :mod:`feedparser`
        structure and passes the work off to :meth:`.get_feed_entries`.

        """
        return self.get_feed_entries(search, search_response)

    def parse_search_result(self, search, result):
        """
        Given a :class:`VideoSearch` instance and a search result (as
        returned by :meth:`.get_search_results`), returns a dictionary
        containing data from the search result, suitable for application via
        :meth:`apply_video_data`. By default, assumes that the ``result`` is a
        :mod:`feedparser` entry and passes the work off to
        :meth:`.parse_feed_entry`.

        """
        return self.parse_feed_entry(result)

    def get_next_search_page_url(self, search, search_response):
        """
        Based on a :class:`VideoSearch` and a ``search_response``, generates
        and returns a url for the next page of the search, or returns ``None``
        if that is not possible. By default, simply returns
        ``None``. Subclasses must override this method to have a meaningful
        search crawl.

        """
        return None
