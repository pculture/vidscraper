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


from vidscraper.errors import CantIdentifyUrl


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

    def suite_for_url(self, url):
        """
        Returns the first registered suite which can handle the url or raises
        :exc:`.CantIdentifyUrl` if no such suite is found.

        """
        for suite in self._suites:
            try:
                if suite.handles_url(url):
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

    # NOTE: In the old scrape suites, there was also a ``link`` field; however,
    # this is subsumed by the video's ``url``

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
            suite = registry.suite_for_url(url)
        elif not suite.handles_url(url):
            raise CantIdentifyUrl
        if fields is None:
            self.fields = list(self._all_fields)
        else:
            self.fields = [f for f in fields if f in self._all_fields]
        self.url = url
        self._suite = suite
        
        # These private attributes are used by scrape suites to determine if
        # the given method of data fetching has already been tried.
        self._oembed = False
        self._api = False
        self._scrape = False

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
        return self.suite.load_video_data(self)


class BaseSuite(object):
    """
    This is a base class for suites, demonstrating the API which is expected
    when interacting with suites. It is not suitable for actual use; some vital
    methods must be defined on a suite-by-suite basis.

    """
    #: A compiled regular expression which will be matched against urls to check
    #: if they are considered handled by this suite.
    regex = None

    #: A set of :class:`.ScrapedVideo` fields that this suite can supply through
    #: an oembed API. Must be supplied by subclasses for accurate optimization.
    oembed_fields = set()
    #: A set of :class:`.ScrapedVideo` fields that this suite can supply through
    #: a site-specific API. Must be supplied by subclasses for accurate
    #: optimization.
    api_fields = set()
    #: A set of :class:`.ScrapedVideo` fields that this suite can supply through
    #: a site-specific scrape. Must be supplied by subclasses for accurate
    #: optimization.
    scrape_fields = set()

    def handles_url(self, url):
        """
        Returns ``True`` if this suite can handle the ``url`` and ``False``
        otherwise. By default, this method will check whether the url matches
        :attr:`.regex` or raise a :exc:`NotImplementedError` if that is not
        possible.

        """
        try:
            return bool(self.regex.match(url))
        except AttributeError:
            raise NotImplementedError

    def get_video(self, url, fields=None):
        """Returns a video using this suite."""
        return ScrapedVideo(url, suite=self, fields=fields)

    def get_oembed_data(self, video):
        """
        Makes an oembed request for the ``video`` and returns a dictionary
        mapping video field names to values. May be implemented by subclasses if
        an oembed API is available.

        """
        raise NotImplementedError

    def get_api_data(self, video):
        """
        Makes an api request for the ``video`` and returns a dictionary
        mapping video field names to values. May be implemented by subclasses if
        an API is available.

        """
        raise NotImplementedError

    def get_scrape_data(self, video):
        """
        Runs a scrape to collect data for the ``video`` and returns a dictionary
        mapping video field names to values. May be implemented by subclasses if
        a page scrape should be supported.

        """
        raise NotImplementedError

    def _count_remaining_fields(self, video, missing_fields, methods):
        """
        Given a video, a set of missing fields and an iterable of methods to
        try, returns the number of fields which would still be missing if those
        methods were run.

        """
        field_set = set()
        if not any([getattr(video, "_%s" % m) for m in methods]):
            for method in methods:
                field_set |= getattr(self, "%s_fields")
        return len(missing_fields - field_set)

    def _run_methods(self, video, methods):
        """
        Runs the selected methods, applies the returned data, and marks on the
        video that they have been run.

        """
        for method in methods:
            data = getattr(self, "get_%s_data" % method)(video)
            for field, value in data.iteritems():
                if (field in video.fields and
                            getattr(video, field) is None):
                    setattr(video, field, value)
            setattr(video, "_%s" % method, True)

    def load_video_data(self, video):
        """
        Makes the smallest requests necessary for loading all the missing fields
        for the ``video``. The data is immediately stored on the video instance.

        """
        if video._oembed and video._api and video._scrape:
            return
        missing_fields = set(video.missing_fields)
        if not missing_fields:
            return

        # Check if the missing fields can be supplied by a single method, a
        # combination of two methods, or all three methods.
        remaining_dict = {}
        for methods in [['ombed'], ['api'], ['scrape'],
                ['oembed', 'api'], ['oembed', 'scrape'], ['api', 'scrape'],
                ['oembed', 'api', 'scrape']]:
            remaining = self._count_remaining_fields(video, missing_fields,
                                                     methods)
            if not remaining:
                self._run_methods(video, methods)
                return
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

    def get_feed_entries(self, feed_url):
        """
        Returns an iterable of feed entries for the feed at ``feed_url``. Must
        be implemented by subclasses.

        """
        raise NotImplementedError

    def parse_feed_entry(self, feed_entry):
        """
        Given a feed entry (as returned by :meth:`.get_feed_entries`), creates
        and returns a :class:`.ScrapedVideo` instance that has data from the
        feed entry pre-stored on it. Must be implemented by subclasses.

        """
        raise NotImplementedError

    def parse_feed(self, feed_url):
        """
        Returns a list of :class:`.ScrapedVideo` instances which have been
        prepopulated with feed data. Internally calls :meth:`.parse_feed_entry`
        on each entry from :meth:`.get_feed_entries`.

        """
        return [self.parse_feed_entry(entry)
                for entry in self.get_feed_entries(feed_url)]

    def get_search_results(self, include_terms, exclude_terms=None,
                           order_by='relevant', **kwargs):
        """
        Returns an iterable of search results for the ``include_terms``,
        ``exclude_terms``, ``order_by``, and other ``kwargs``. Must be
        implemented by subclasses.

        """
        raise NotImplementedError

    def parse_search_result(self, result):
        """
        Given a search result (as returned by :meth:`.get_search_results`),
        creates and returns a :class:`.ScrapedVideo` instance that has data from
        the search result pre-stored on it. Must be implemented by subclasses.

        """
        raise NotImplementedError

    def search(self, url, include_terms, exclude_terms=None,
               order_by='relevant', **kwargs):
        """
        Runs a search for the given parameters and returns a list of
        :class:`.ScrapedVideo` instances which have been prepopulated with data
        from the search. Internally calls :meth:`.parse_search_result` on each
        result from :meth:`.get_search_results`.

        """
        return [self.parse_search_result(result) for result in
                self.get_search_results(include_terms,
                    exclude_terms=exclude_terms, order_by=order_by, **kwargs)]
