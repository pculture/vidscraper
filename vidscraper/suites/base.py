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

import re
import urllib
import urllib2

import feedparser

from vidscraper.compat import json
from vidscraper.errors import CantIdentifyUrl, VideoDeleted
from vidscraper.utils.feedparser import (struct_time_to_datetime,
                                         get_item_thumbnail_url)
from vidscraper.utils.search import (search_string_from_terms,
                                     terms_from_search_string)

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


class Video(object):
    """
    This is the class which should be used to represent videos which are
    returned by suite scraping, searching and feed parsing.

    :param url: The "pasted" url for the video.
    :param suite: The suite to use for the video. This does not need to be a
                  registered suite, but it does need to handle the video's
                  ``url``. If no suite is provided, one will be auto-selected
                  based on the ``url``.
    :param fields: A list of fields which should be fetched for the video. This
                  may be used to optimize the fetching process.

    """
    # FIELDS
    _all_fields = (
        'title', 'description', 'publish_datetime', 'file_url',
        'file_url_mimetype', 'file_url_length', 'file_url_expires',
        'flash_enclosure_url', 'is_embeddable', 'embed_code',
        'thumbnail_url', 'user', 'user_url', 'tags', 'link', 'guid',
        'index', 'license'
    )
    #: The canonical link to the video. This may not be the same as the url
    #: used to initialize the video.
    link = None
    #: A (supposedly) global identifier for the video
    guid = None
    #: Where the video was in the feed/search
    index = None
    #: The video's title.
    title = None
    #: A text or html description of the video.
    description = None
    #: A python datetime indicating when the video was published.
    publish_datetime = None
    #: The url to the actual video file.
    file_url = None
    #: The MIME type for the actual video file
    file_url_mimetype = None
    #: The length of the actual video file
    file_url_length = None
    #: a datetime.datetime() representing when we think the file URL is no
    #: longer valid
    file_url_expires = None
    #: "Crappy enclosure link that doesn't actually point to a url.. the kind
    #: crappy flash video sites give out when they don't actually want their
    #: enclosures to point to video files."
    flash_enclosure_url = None
    #: The actual embed code which can be used for displaying the video in a
    #: browser.
    embed_code = None
    #: The url for a thumbnail of the video.
    thumbnail_url = None
    #: The username associated with the video.
    user = None
    #: The url associated with the video's user.
    user_url = None
    #: A list of tag names associated with the video.
    tags = None
    #: A URL to a description of the license the Video is under (often Creative
    #: Commons)
    license = None

    # These were pretty suite-specific and should perhaps be treated as such?
    #: Whether the video is embeddable? (Youtube)
    is_embeddable = None

    # OTHER ATTRS
    #: The url for this video to scrape based on.
    url = None
    #: An iterable of fields to be fetched for this video. Other fields will
    #: not populated during scraping.
    fields = None

    def __init__(self, url, suite=None, fields=None, api_keys=None):
        if suite is None:
            suite = registry.suite_for_video_url(url)
        elif not suite.handles_video_url(url):
            raise CantIdentifyUrl
        if fields is None:
            self.fields = list(self._all_fields)
        else:
            self.fields = [f for f in fields if f in self._all_fields]
        self.url = url
        self._suite = suite
        self.api_keys = api_keys if api_keys is not None else {}

        # This private attribute is set to ``True`` when data is loaded into
        # the video by a scrape suite. It is *not* set when data is pre-loaded
        # from a feed or a search.
        self._loaded = False

    @property
    def missing_fields(self):
        """
        Returns a list of fields which have been requested but which have not
        been filled with data.

        """
        return [f for f in self.fields if getattr(self, f) is None]

    @property
    def suite(self):
        """The suite to be used for scraping this video."""
        return self._suite

    def load(self):
        """Uses the video's :attr:`suite` to fetch the fields for the video."""
        if not self._loaded:
            self.suite.load_video_data(self)
            self._loaded = True

    def is_loaded(self):
        return self._loaded


class BaseVideoIterator(object):
    """
    Generic base class for url-based iterators which rely on suites to yield
    :class:`Video` instances. :class:`VideoFeed` and
    :class:`VideoSearch` both subclass :class:`BaseVideoIterator`.
    """
    _first_response = None
    _max_results = None

    @property
    def max_results(self):
        """
        The maximum number of results for this iterator, or ``None`` if there
        is no maximum.

        """
        return self._max_results

    def get_first_url(self):
        """
        Returns the first url which this iterator is expected to handle.
        """
        raise NotImplementedError

    def get_url_response(self, url):
        raise NotImplementedError

    def handle_first_response(self, response):
        self._first_response = response 

    def get_response_items(self, response):
        raise NotImplementedError

    def get_item_data(self, item):
        raise NotImplementedError

    def get_next_url(self, response):
        raise NotImplementedError

    def load(self):
        if self._first_response:
            return self._first_response
        url = self.get_first_url()
        response = self.get_url_response(url)
        self.handle_first_response(response)
        return response

    def _data_from_item(self, item):
        """
        Returns a :class:`Video` given some data from a feed.
        """
        data = self.get_item_data(item)
        video = self.suite.get_video(data['link'],
                                     fields=self.fields,
                                     api_keys=self.api_keys)
        self.suite.apply_video_data(video, data)
        return video

    def __iter__(self):
        try:
            response = self.load()
            item_count = 1
            # decrease the index as we count down through the entries.  doesn't
            # quite work for feeds where we don't know the /total/ number of
            # items; then it'll just index the video within the one feed
            while self._max_results is None or item_count < self._max_results:
                items = self.get_response_items(response)
                for item in items:
                    try:
                        video = self._data_from_item(item)
                    except VideoDeleted:
                        continue
                    video.index = item_count
                    yield video
                    if self._max_results is not None:
                        if item_count >= self._max_results:
                            raise StopIteration
                    item_count += 1

                # We haven't hit the limit yet. Continue to the next page if:
                # - crawl is enabled
                # - the current page was not empty
                # - a url can be calculated for the next page.
                url = None
                if self.crawl and items:
                    url = self.get_next_url(response)
                if url is None:
                    break
                response = self.get_url_response(url)
        except NotImplementedError:
            pass
        raise StopIteration


class VideoFeed(BaseVideoIterator):
    """
    Represents a feed that has been scraped from a website. Note that the term
    "feed" in this context simply means a list of videos which can be found at
    a certain url. The source could as easily be an API, a search result rss
    feed, or a video list page which is literally scraped.
    
    :param url: The url to be scraped.
    :param suite: The suite to use for the scraping. If none is provided, one
                  will be selected based on the url.
    :param fields: Passed on to the :class:`Video` instances which are
                   created by this feed.
    :param crawl: If ``True``, then the scrape will continue onto subsequent
                  pages of the feed if that is supported by the suite. The
                  request for the next page will only be executed once the
                  current page is exhausted. Default: ``False``.
    :param max_results: The maximum number of results to return from iteration.
                        Default: ``None`` (as many as possible.)
    :param api_keys: A dictionary of any API keys which may be required for the
                     suite used by this feed.
    :param last_modified: A last-modified date which may be sent to the service
                          provider to try to short-circuit fetching a feed
                          whose contents are already known.
    :param etag: An etag which may be sent to the service provider to try to
                 short-circuit fetching a feed whose contents are already
                 known.

    Additionally, :class:`VideoFeed` populates the following attributes after
    fetching its first response. Attributes which are not supported by the
    feed's suite or which have not been populated will be ``None``.

    .. attr:: entry_count
        The estimated number of entries for this search.

    .. attr:: last_modified
        A python datetime representing when the feed was last changed. Before
        fetching the first response, this will be equal to the
        ``last_modified`` date the :class:`VideoFeed` was instantiated with.

    .. attr:: etag
        A marker representing a feed's current state. Before fetching the first
        response, this will be equal to the ``etag`` the :class:`VideoFeed`
        was instantiated with.

    .. attr:: description
        A description of the feed.

    .. attr:: webpage
        The url for an html, human-readable version of the feed.

    .. attr:: title
        The title of the feed.

    .. attr:: thumbnail_url
        A URL for a thumbnail representing the whole feed.

    .. attr:: guid
        A unique identifier for the feed.

    """

    def __init__(self, url, suite=None, fields=None, crawl=False,
                 max_results=None, api_keys=None, last_modified=None,
                 etag=None):
        self.original_url = url
        if suite is None:
            suite = registry.suite_for_feed_url(url)
        elif not suite.handles_feed_url(url):
            raise CantIdentifyUrl
        self.url = suite.get_feed_url(url)
        self.suite = suite
        self.fields = fields
        self.crawl = crawl
        self._max_results = max_results
        self.api_keys = api_keys if api_keys is not None else {}
        self.last_modified = last_modified
        self.etag = etag

        self.entry_count = None
        self.description = None
        self.webpage = None
        self.title = None
        self.thumbnail_url = None
        self.guid = None

    @property
    def parsed_feed(self):
        if not self._first_response:
            self.load()
        return self._first_response

    def get_first_url(self):
        return self.url

    def get_url_response(self, url):
        return self.suite.get_feed_response(self, url)

    def handle_first_response(self, response):
        super(VideoFeed, self).handle_first_response(response)
        response = self.suite.get_feed_info_response(self, response)
        self.title = self.suite.get_feed_title(self, response)
        self.entry_count = self.suite.get_feed_entry_count(self, response)
        self.description = self.suite.get_feed_description(self, response)
        self.webpage = self.suite.get_feed_webpage(self, response)
        self.thumbnail_url = self.suite.get_feed_thumbnail_url(self, response)
        self.guid = self.suite.get_feed_guid(self, response)
        self.last_modified = self.suite.get_feed_last_modified(self, response)
        self.etag = self.suite.get_feed_etag(self, response)

    def get_response_items(self, response):
        return self.suite.get_feed_entries(self, response)

    def get_item_data(self, item):
        return self.suite.parse_feed_entry(item)

    def get_next_url(self, response):
        return self.suite.get_next_feed_page_url(self, response)


class VideoSearch(BaseVideoIterator):
    """
    Represents a search against a suite. Iterating over a
    :class:`VideoSearch` instance will execute the search and yield
    :class:`Video` instances for the results of the search.

    :param query: The raw string for the search.
    :param suite: Suite to use for this search.
    :param fields: Passed on to the :class:`Video` instances which are
                   created by this search.
    :param order_by: The ordering to apply to the search results. If a suite
                     does not support the given ordering, it will return an
                     empty list. Possible values: ``relevant``, ``latest``,
                     ``popular``, ``None`` (use the default ordering of the
                     suite's service provider). Values may be prefixed with a
                     "-" to indicate descending ordering. Default: ``None``.
    :param crawl: If ``True``, then the search will continue on to subsequent
                  pages if the suite supports it. The request for the next page
                  will only be executed once the current page is exhausted.
                  Default: ``False``.
    :param max_results: The maximum number of results to return from iteration.
                        Default: ``None`` (as many as possible).
    :param api_keys: A dictionary of any API keys which may be required for the
                     suite used by this search.

    Additionally, VideoSearch supports the following attributes:

    .. attr:: total_results
        The estimated number of total results for this search, if supported by
        the suite. Otherwise, ``None``.

    .. attr:: time
        The amount of time required by the remote service to execute the query,
        if supported by the suite. Otherwise, ``None``.

    """

    @property
    def max_results(self):
        return self._max_results

    def __init__(self, query, suite, fields=None, order_by=None,
                 crawl=False, max_results=None, api_keys=None):
        self.include_terms, self.exclude_terms = terms_from_search_string(
            query)
        self.query = search_string_from_terms(self.include_terms,
                                              self.exclude_terms)
        self.raw_query = query
        self.suite = suite
        self.fields = fields
        self.order_by = order_by
        self.crawl = crawl
        self._max_results = max_results
        self.api_keys = api_keys if api_keys is not None else {}

        self.total_results = None
        self.time = None

    def get_first_url(self):
        return self.suite.get_search_url(self)

    def get_url_response(self, url):
        return self.suite.get_search_response(self, url)

    def handle_first_response(self, response):
        super(VideoSearch, self).handle_first_response(response)
        self.total_results = self.suite.get_search_total_results(self,
                                                                 response)
        self.time = self.suite.get_search_time(self, response)

    def get_response_items(self, response):
        return self.suite.get_search_results(self, response)

    def get_item_data(self, item):
        return self.suite.parse_search_result(self, item)

    def get_next_url(self, response):
        return self.suite.get_next_search_page_url(self, response)


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

    #: A URL which is an endpoint for an oembed API.
    oembed_endpoint = None

    @property
    def oembed_fields(self):
        """
        A set of :class:`.Video` fields that this suite can supply
        through an oembed API. By default, this will be empty if
        :attr:`.oembed_endpoint` is ``None`` and a base set of commonly
        available fields otherwise.

        """
        if self.oembed_endpoint is None:
            return set()
        return set(['title', 'user', 'user_url', 'thumbnail_url',
                    'embed_code'])

    #: A set of :class:`.Video` fields that this suite can supply
    #through : a site-specific API. Must be supplied by subclasses for accurate
    #: optimization.
    api_fields = set()
    #: A set of :class:`.Video` fields that this suite can supply
    #through : a site-specific scrape. Must be supplied by subclasses for
    #accurate : optimization.
    scrape_fields = set()

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
        Returns a set of all of the fields we could possible get from this
        suite.
        """
        return self.oembed_fields | self.api_fields | self.scrape_fields

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

    def apply_video_data(self, video, data):
        """
        Stores values from a ``data`` dictionary on the corresponding
        attributes of a :class:`Video` instance.

        """
        for field, value in data.iteritems():
            if (field in video.fields):# and getattr(video, field) is None):
                setattr(video, field, value)

    def get_oembed_url(self, video):
        """
        Returns the url for fetching oembed data. By default, generates an
        oembed request url based on :attr:`.oembed_endpoint` or raises
        :exc:`NotImplementedError` if that is not defined.

        """
        endpoint = self.oembed_endpoint
        if endpoint is None:
            raise NotImplementedError
        return u'%s?url=%s' % (endpoint, urllib.quote_plus(video.url))

    def parse_oembed_response(self, response_text):
        """
        Parses oembed response text into a dictionary mapping
        :class:`Video` field names to values. By default, this assumes
        that the commonly-available fields ``title``, ``author_name``,
        ``author_url``, ``thumbnail_url``, and ``html`` are available.

        """
        parsed = json.loads(response_text)
        data = {
            'title': parsed['title'],
            'user': parsed['author_name'],
            'user_url': parsed['author_url'],
            'thumbnail_url': parsed['thumbnail_url'],
            'embed_code': parsed['html']
        }
        return data

    def parse_oembed_error(self, exc):
        """
        Parses a :module:`urllib` exception raised during the OEmbed request.
        If we re-raise an exception, that's it; otherwise, the dictionary
        returned will be used to populate the :class:`Video` object.

        By default, just re-raises the given exception.
        """
        raise exc

    def get_api_url(self, video):
        """
        Returns the url for fetching API data. May be implemented by
        subclasses if an API is available.

        """
        raise NotImplementedError

    def parse_api_response(self, response_text):
        """
        Parses API response text into a dictionary mapping
        :class:`Video` field names to values. May be implemented by
        subclasses if an API is available.

        """
        raise NotImplementedError

    def parse_api_error(self, exc):
        """
        Parses a :module:`urllib` exception raised during the API request.
        If we re-raise an exception, that's it; otherwise, the dictionary
        returned will be used to populate the :class:`Video` object.

        By default, just re-raises the given exception.
        """
        raise exc

    def get_scrape_url(self, video):
        """
        Returns the url for fetching scrape data. May be implemented by
        subclasses if a page scrape should be supported.

        """
        raise NotImplementedError

    def parse_scrape_response(self, response_text):
        """
        Parses scrape response text into a dictionary mapping
        :class:`Video` field names to values. May be implemented by
        subclasses if a page scrape should be supported.

        """
        raise NotImplementedError

    def parse_scrape_error(self, exc):
        """
        Parses a :module:`urllib` exception raised during the scrape request.
        If we re-raise an exception, that's it; otherwise, the dictionary
        returned will be used to populate the :class:`Video` object.

        By default, just re-raises the given exception.
        """
        raise exc

    def _run_methods(self, video, methods):
        """
        Runs the selected methods, applies the returned data, and marks on the
        video that they have been run.

        """
        for method in methods:
            url = getattr(self, "get_%s_url" % method)(video)
            try:
                response_text = urllib2.urlopen(url, timeout=5).read()
            except Exception, exc:
                # if an exception is raised in this method, it isn't caught and
                # shows up to the user
                data = getattr(self, 'parse_%s_error' % method)(exc)
            else:
                data = getattr(self, "parse_%s_response" % method)(response_text)
            self.apply_video_data(video, data)

    def load_video_data(self, video):
        """
        Makes the smallest requests necessary for loading all the missing
        fields for the ``video``. The data is immediately stored on the video
        instance.

        """
        missing_fields = set(video.missing_fields)
        if not missing_fields:
            return

        # Check if the missing fields can be supplied by a single method, a
        # combination of two methods, or all three methods.
        remaining_dict = {}
        for methods in [['oembed'], ['api'], ['scrape'],
                ['oembed', 'api'], ['oembed', 'scrape'], ['api', 'scrape'],
                ['oembed', 'api', 'scrape']]:
            field_set = set()
            for method in methods:
                field_set |= getattr(self, "%s_fields" % method)
            remaining = len(missing_fields - field_set)

            # If a method fills all the missing fields, take it immediately.
            if not remaining:
                self._run_methods(video, methods)
                return

            # Otherwise only consider the method if it would reduce the number
            # of remaining fields at all.
            if remaining < len(missing_fields):
                remaining_dict.setdefault(remaining, []).append(methods)

        # If we get here, it means that it is impossible to supply all the
        # requested fields. So we try to get as close as possible with as few
        # queries as possible. We run the first entry in the best-performing
        # slot, since that will also have been the earliest in the original
        # order. If this doesn't end up doing anything, then there is nothing
        # to be done and we can simply return.
        for i in xrange(len(missing_fields)):
            if i in remaining_dict:
                self._run_methods(video, remaining_dict[i][0])
                return

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
        if 'updated_parsed' in feed_response.feed:
            return struct_time_to_datetime(feed_response.feed.updated_parsed)
        if 'published_parsed' in feed_response.feed:
            return struct_time_to_datetime(feed_response.feed.published_parsed)
        return None

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
