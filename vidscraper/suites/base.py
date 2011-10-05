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
from vidscraper.errors import CantIdentifyUrl
from vidscraper.utils.search import (intersperse_results,
                search_string_from_terms, terms_from_search_string)


class SuiteRegistry(object):
    """
    A registry of suites. Suites may be registered, unregistered, and iterated
    over.

    """

    def __init__(self):
        self._suites = []
        self._suite_dict = {}

    @property
    def suites(self):
        """Returns a tuple of registered suites."""
        return tuple(self._suites)

    def register(self, suite):
        """Registers a suite if it is not already registered."""
        if suite not in self._suite_dict:
            self._suite_dict[suite] = suite()
            self._suites.append(self._suite_dict[suite])

    def unregister(self, suite):
        """Unregisters a suite if it is registered."""
        if suite in self._suite_set:
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
        raise CantIdentifyUrl


#: An instance of :class:`.SuiteRegistry` which is used by :mod:`vidscraper` to
#: track registered suites.
registry = SuiteRegistry()


class ScrapedVideo(object):
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
        'file_url_is_flaky', 'flash_enclosure_url', 'is_embeddable',
        'embed_code', 'thumbnail_url', 'user', 'user_url', 'tags', 'link'
    )
    #: The canonical link to the video. This may not be the same as the url
    #: used to initialize the video.
    link = None
    #: The video's title.
    title = None
    #: A text or html description of the video.
    description = None
    #: A python datetime indicating when the video was published.
    publish_datetime = None
    #: The url to the actual video file.
    file_url = None
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

    # These were pretty suite-specific and should perhaps be treated as such?
    #: Whether the video is embeddable? (Youtube)
    is_embeddable = None
    #: Whether the url can be relied on or is temporary for some reason (such as
    #: depending on session data). (Vimeo)
    file_url_is_flaky = None

    # OTHER ATTRS
    #: The url for this video to scrape based on.
    url = None
    #: An iterable of fields to be fetched for this video. Other fields will not
    #: be populated during scraping.
    fields = None

    def __init__(self, url, suite=None, fields=None):
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
        
        # This private attribute is set to ``True`` when data is loaded into the
        # video by a scrape suite. It is *not* set when data is pre-loaded from
        # a feed or a search.
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


class ScrapedFeed(object):
    """
    Represents a feed that has been scraped from a website. Note that the term
    "feed" in this context simply means a list of videos which can be found at a
    certain url. The source could as easily be an API, a search result rss feed,
    or a video list page which is literally scraped.

    """
    #: The url used to initialize the feed.
    url = None

    def __init__(self, url, suite=None, fields):
        """
        
        """

api_keys = {
    'vimeo_secret': xxx,
    'vimeo_key': yyy,
}
class ScrapedSearch(object):
    """
    Represents a search against a suite. Can be iterated over to return
    ScrapedVideo instances for the results of the search.

    :param query: The raw string for the search.
    :param suite: Suite to use for this search.
    :param fields: Passed on to the :class:`ScrapedVideo` instances which are
                   created by this feed.
    :param order_by: The ordering to apply to the search results. If a suite
                     does not support the given ordering, it will return an
                     empty list. Possible values: ``relevant``, ``latest``,
                     ``popular``. Values may be prefixed with a "-" to indicate
                     descending ordering. Default: ``-relevant``.
    :param crawl: If ``True``, then the search will continue on to subsequent
                  pages if the suite supports it. Default: ``False``.
    :param max_results: The maximum number of results to return from iteration.
                        Default: ``None`` (as many as possible).
    :param api_keys: A dictionary of any API keys which may be required for any
                     of the suites used by this search.

    """
    total_results = None

    @property
    def max_results(self):
        return self._max_results

    def __init__(self, query, suite, fields=None, order_by='-relevant',
                 crawl=False, max_results=None, api_keys=None):
        self.include_terms, self.exclude_terms = terms_from_search_string(query)
        self.query = search_string_from_terms(self.include_terms,
                                              self.exclude_terms)
        self.raw_query = query
        self.suite = suite
        self.fields = fields
        self.order_by = order_by
        self.crawl = crawl
        self._max_results = max_results
        self.api_keys = api_keys if api_keys is not None else {}

    def __iter__(self):
        # NOTE: This should perhaps save the results to a _result_cache?
        search_url = self.suite.get_search_url(self)

        result_count = 0
        while result_count < self.max_results:
            search_response = self.suite.get_search_response(self, search_url)
            results = self.suite.get_search_results(self, search_response)
            for result in results:
                data = self.suite.parse_search_result(self, result)
                video = self.suite.get_video(data['link'], fields)
                self.suite.apply_video_data(video, data)
                yield video
                result_count += 1
                if result_count >= self.max_results:
                    break
            else:
                # We haven't hit the limit yet. Continue to the next page if
                # crawl is enabled and the current page was not empty.
                if crawl and results:
                    search_url = self.suite.get_next_search_page_url(self,
                                            search_response, search_string,
                                            order_by, **kwargs)
                else:
                    break
        raise StopIteration


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
        A set of :class:`.ScrapedVideo` fields that this suite can supply
        through an oembed API. By default, this will be empty if
        :attr:`.oembed_endpoint` is ``None`` and a base set of commonly
        available fields otherwise.

        """
        if self.oembed_endpoint is None:
            return set()
        return set(['title', 'user', 'user_url', 'thumbnail_url', 'embed_code'])

    #: A set of :class:`.ScrapedVideo` fields that this suite can supply through
    #: a site-specific API. Must be supplied by subclasses for accurate
    #: optimization.
    api_fields = set()
    #: A set of :class:`.ScrapedVideo` fields that this suite can supply through
    #: a site-specific scrape. Must be supplied by subclasses for accurate
    #: optimization.
    scrape_fields = set()

    def __init__(self):
        if isinstance(self.video_regex, basestring):
            self.video_regex = re.compile(self.video_regex)
        if isinstance(self.feed_regex, basestring):
            self.feed_regex = re.compile(self.feed_regex)

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
            return bool(self.video_regex.match(url))
        except AttributeError:
            raise NotImplementedError

    def get_video(self, url, fields=None):
        """Returns a video using this suite."""
        return ScrapedVideo(url, suite=self, fields=fields)

    def apply_video_data(self, video, data):
        """
        Stores values from a ``data`` dictionary on the corresponding attributes
        of a :class:`ScrapedVideo` instance.

        """
        for field, value in data.iteritems():
            if (field in video.fields and getattr(video, field) is None):
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
        :class:`ScrapedVideo` field names to values. By default, this assumes
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

    def get_api_url(self, video):
        """
        Returns the url for fetching API data. May be implemented by
        subclasses if an API is available.

        """
        raise NotImplementedError

    def parse_api_response(self, response_text):
        """
        Parses API response text into a dictionary mapping
        :class:`ScrapedVideo` field names to values. May be implemented by
        subclasses if an API is available.

        """
        raise NotImplementedError

    def get_scrape_url(self, video):
        """
        Returns the url for fetching scrape data. May be implemented by
        subclasses if a page scrape should be supported.

        """
        raise NotImplementedError

    def parse_scrape_response(self, response_text):
        """
        Parses scrape response text into a dictionary mapping
        :class:`ScrapedVideo` field names to values. May be implemented by
        subclasses if a page scrape should be supported.

        """
        raise NotImplementedError

    def _run_methods(self, video, methods):
        """
        Runs the selected methods, applies the returned data, and marks on the
        video that they have been run.

        """
        for method in methods:
            url = getattr(self, "get_%s_url" % method)(video)
            response_text = urllib2.urlopen(url, timeout=5).read()
            data = getattr(self, "parse_%s_response" % method)(response_text)
            self.apply_video_data(video, data)

    def load_video_data(self, video):
        """
        Makes the smallest requests necessary for loading all the missing fields
        for the ``video``. The data is immediately stored on the video instance.

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

    def get_feed_response(self, feed_url):
        """
        Returns a parsed response for this feed. By default, this uses
        :mod:`feedparser` to get a response for the ``feed_url`` and returns the
        resulting structure.

        """
        return feedparser.parse(feed_url)

    def get_feed_entries(self, feed_response):
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

    def get_next_feed_page_url(self, last_url, feed_response):
        """
        Based on a ``feed_response`` and the ``last_url`` used for this feed,
        generates and returns a url for the next page of the feed, or returns
        ``None`` if that is not possible. By default, simply returns ``None``.
        Subclasses must override this method to have a meaningful feed crawl.

        """
        return None

    def get_feed(self, feed_url, fields=None, crawl=False):
        """
        Returns a generator which yields :class:`.ScrapedVideo` instances that
        have been prepopulated with feed data. Internally calls
        :meth:`.get_feed_response` and :meth:`.get_feed_entries`, then calls
        :meth:`.parse_feed_entry` on each entry found. If ``crawl`` is ``True``
        (not the default) then subsequent pages of the feed will be looked for
        with :meth:`.get_next_feed_page_url`. If any are found, they will also
        be loaded and parsed.

        .. warning:: Crawl will continue until it has loaded all pages or until
                     a page comes back empty. This can take a significant amount
                     of time.

        """
        next_url = feed_url
        while next_url:
            feed_response = self.get_feed_response(next_url)
            entries = self.get_feed_entries(feed_response)
            for entry in entries:
                data = self.parse_feed_entry(entry)
                video = self.get_video(data['link'], fields)
                self.apply_video_data(video, data)
                yield video
            if not crawl or not entries:
                next_url = None
            else:
                next_url = self.get_next_feed_page_url(next_url, feed_response)
        raise StopIteration

    def get_search_url(self, search_string, order_by=None, **kwargs):
        """
        Returns a url which this suite can use to fetch search results for the
        given string. Must be implemented by subclasses.

        """
        raise NotImplementedError

    def get_search_response(self, search_url, **kwargs):
        """
        Returns a parsed response for the given ``search_url``. By default,
        assumes that the url references a feed and passes the work off to
        :meth:`.get_feed_response`.

        """
        return self.get_feed_response(search_url)

    def get_search_results(self, search_response):
        """
        Returns an iterable of search results for a ``search_response`` as
        returned by :meth:`.get_search_response`. By default, assumes that the
        ``search_response`` is a :mod:`feedparser` structure and passes the work
        off to :meth:`.get_feed_entries`.

        """
        return self.get_feed_entries(search_response)

    def parse_search_result(self, result):
        """
        Given a search result (as returned by :meth:`.get_search_results`),
        returns a dictionary containing data from the search result, suitable
        for application via :meth:`apply_video_data`. By default, assumes that
        the ``result`` is a :mod:`feedparser` entry and passes the work off to
        :meth:`.parse_feed_entry`.

        """
        return self.parse_feed_entry(result)

    def get_next_search_page_url(self, search_response, search_string,
                                 order_by=None, **kwargs):
        """
        Based on the ``search_response`` and the other :meth:`.get_search_url`
        arguments, generates and returns a url for the next page of the search,
        or returns ``None`` if that is not possible. By default, simply returns
        ``None``. Subclasses must override this method to have a meaningful
        search crawl.

        """
        return None

    def search(self, include_terms, exclude_terms=None,
               order_by=None, fields=None, crawl=False, **kwargs):
        """
        Returns a generator which yields :class:`.ScrapedVideo` instances that have been prepopulated with data from the search. Internally calls :meth:`.get_search_url`, :meth:`.get_search_response`, and :meth:`.get_search_results`, then calls :meth:`.parse_search_result` on each result found. If ``crawl`` is ``True`` (not the default) then subsequent pages of search results will be looked for with :meth:`.get_next_search_page_url`. If any are found, they will also be loaded and parsed.

        ``order_by`` may be either "relevant" or "latest". Other values will be
        ignored. If a value is passed in, suites which do not support that value
        should return an empty result set.

        Any additional ``kwargs`` will be passed into the calls to
        :meth:`.get_search_url`, :meth:`.get_search_response`, and
        :meth:`get_next_search_page_url`. This can be used, for example, to
        provide authentication support for a specific suite without interfering
        with the operation of other suites.

        .. warning:: Crawl will continue until it has loaded all pages or until
                     a page comes back empty. This can take a significant amount
                     of time.

        """
        search_string = search_string_from_terms(include_terms, exclude_terms)
        search_url = self.get_search_url(search_string, order_by, **kwargs)

        while search_url:
            search_response = self.get_search_response(search_url, **kwargs)
            results = self.get_search_results(search_response)
            for result in results:
                data = self.parse_search_result(result)
                video = self.get_video(data['link'], fields)
                self.apply_video_data(video, data)
                yield video
            if not crawl or not results:
                search_url = None
            else:
                search_url = self.get_next_search_page_url(search_response,
                                            search_string, order_by, **kwargs)
        raise StopIteration
