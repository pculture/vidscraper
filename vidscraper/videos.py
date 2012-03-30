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

import urllib

from vidscraper.errors import CantIdentifyUrl, VideoDeleted
from vidscraper.utils.search import (search_string_from_terms,
                                     terms_from_search_string)


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
    #: Whether the video is embeddable? (Youtube, Vimeo)
    is_embeddable = None

    # OTHER ATTRS
    #: The url for this video to scrape based on.
    url = None
    #: An iterable of fields to be fetched for this video. Other fields will
    #: not populated during scraping.
    fields = None

    def __init__(self, url, suite=None, fields=None, api_keys=None):
        from vidscraper.suites import registry
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
            data = self.suite.run_methods(self)
            self._apply(data)
            self._loaded = True

    def _apply(self, data):
        """
        Stores values from a ``data`` dictionary in the corresponding fields
        on this instance.
        """
        fields = set(data) & set(self.fields)
        for field in fields:
            setattr(self, field, data[field])

    def is_loaded(self):
        return self._loaded


class BaseVideoIterator(object):
    """
    Generic base class for url-based iterators which rely on suites to yield
    :class:`Video` instances. :class:`VideoFeed` and
    :class:`VideoSearch` both subclass :class:`BaseVideoIterator`.
    """
    per_page = None
    page_url_format = None

    def __init__(self, start_index=1, max_results=None, video_fields=None,
                 api_keys=None):
        self.start_index = start_index
        self.max_results = max_results
        self.video_fields = video_fields
        self.api_keys = api_keys if api_keys is not None else {}
        self._loaded = False

        self.item_count = 0
        self._page_videos_iter = None
        self._response = None

    def __iter__(self):
        return self

    def next(self):
        if (self.max_results is not None and
            self.item_count >= self.max_results):
            raise StopIteration

        if self._response is None:
            self._next_page()

        try:
            video = self._page_videos_iter.next()
        except StopIteration:
            # We're done with this page; try the next one.
            self._response = None
            self._page_videos_iter = None
            return self.next()
        else:
            self.item_count += 1
            return video

    def _next_page(self):
        page_start = self.start_index + self.item_count
        if self.max_results is None:
            page_max = self.per_page
        else:
            page_max = self.max_results - self.item_count
            if self.per_page is not None:
                page_max = min(page_max, self.per_page)

        r = self.get_page(page_start, page_max)
        self._response = r
        self._page_videos_iter = self._page_videos(r, page_max)

    def _page_videos(self, response, max_results=None):
        items = self.get_response_items(response)
        item_count = 0
        for item in items:
            data = self.get_item_data(item)
            video = Video(data['link'], fields=self.video_fields,
                          api_keys=self.api_keys)

            video._apply(data)
            item_count += 1
            yield video
            if max_results is not None and item_count >= max_results:
                raise StopIteration

    def load(self):
        if not self._loaded:
            if self._response is None:
                self._next_page()
            data = self.data_from_response(self._response)
            self._apply(data)
            self._loaded = True

    def _apply(self, data):
        fields = set(data) & set(self._all_fields)
        for field in fields:
            setattr(self, field, data[field])

    def get_response_items(self, response):
        raise NotImplementedError

    def get_item_data(self, item):
        raise NotImplementedError

    def get_page_url(self, page_start, page_max):
        if self.page_url_format is None:
            raise NotImplementedError
        format_data = self.get_page_url_data()
        format_data.update({
            'page_start': page_start,
            'page_max': page_max
        })
        return self.page_url_format % format_data

    def get_page_url_data(self):
        return {}

    def get_page(self, page_start, page_max):
        raise NotImplementedError

    def data_from_response(self, response):
        raise NotImplementedError


class FeedparserVideoIteratorMixin(object):
    def get_page(self, start_index, max_results):
        url = self.get_page_url(start_index, max_results)
        response = feedparser.parse(url, etag=self.etag, modified=self.modified)
        # Don't let feedparser silence connection problems.
        if isinstance(response.get('bozo_exception', None), urllib2.URLError):
            raise response.bozo_exception
        return response

    def data_from_response(self, response):
        feed = response.feed
        data = {
            'title': feed.get('title'),
            'video_count': len(response.entries),
            'description': feed.get('subtitle'),
            'webpage': feed.get('link'),
            'guid': feed.get('id'),
            'etag': response.get('etag'),
        }
        try:
            data['thumbnail_url'] = get_item_thumbnail_url(feed)
        except KeyError:
            pass

        # Should this be using response.modified?
        parsed = feed.get('updated_parsed') or feed.get('published_parsed')
        if parsed:
            data['last_modified'] = struct_time_to_datetime(parsed)

        return data

    def get_response_items(self, response):
        return response.entries


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
    _all_fields = ('video_count', 'last_modified', 'etag', 'description',
                   'webpage', 'title', 'thumbnail_url', 'guid')

    video_count = None
    description = None
    webpage = None
    title = None
    thumbnail_url = None
    guid = None

    def __init__(self, url, last_modified=None, etag=None, **kwargs):
        super(VideoFeed, self).__init__(**kwargs)

        self.url = url
        self.url_data = self.get_url_data(url)
        self.last_modified = last_modified
        self.etag = etag

    def get_url_data(self, url):
        """
        Parses the url into data which can be used to construct page urls.

        """
        return {'url': url}

    def get_page_url_data(self):
        return self.url_data.copy()


class FeedparserVideoFeed(FeedparserVideoIteratorMixin, VideoFeed):
    pass


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
    _all_fields = ('video_count',)
    video_count = None

    def __init__(self, query, order_by=None, **kwargs):
        super(VideoSearch, self).__init__(**kwargs)
        # Normalize the search
        self.include_terms, self.exclude_terms = terms_from_search_string(
            query)
        self.query = search_string_from_terms(self.include_terms,
                                              self.exclude_terms)
        self.raw_query = query
        self.order_by = order_by

    def get_page_url_data(self):
        return {
            'query': urllib.quote_plus(self.query),
            'order_by': self.order_by
        }


class FeedparserVideoSearch(FeedparserVideoIteratorMixin, VideoSearch):
    pass
