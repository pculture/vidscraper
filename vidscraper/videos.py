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

import math
import urllib
import urllib2

import feedparser

from vidscraper.exceptions import UnhandledURL, VideoDeleted
from vidscraper.utils.feedparser import (get_item_thumbnail_url,
                                         struct_time_to_datetime)
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
            raise UnhandledURL
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
    Generic base class for iterating over groups of videos spread across
    multiple urls - for example, an rss feed, an api response, or a video list
    page.

    :param start_index: The index of the first video to return. Default: 1.
    :type start_index: integer >= 1
    :param max_results: The maximum number of videos to return. If this is
                        ``None``, as many videos as possible will be returned.
    :param video_fields: Fields to be passed to any created :class:`Video`
                         instances.
    :param api_keys: A dictionary of api keys.

    """
    #: Describes the number of videos expected on each page. This should be
    #: set whether or not the number of videos per page can be controlled.
    per_page = None

    #: A format string which will be used to build page urls for this
    #: iterator. This should use the {} format described under str.format()
    #: in the python docs:
    #: http://docs.python.org/library/stdtypes.html#str.format
    page_url_format = None

    def __init__(self, start_index=1, max_results=None, video_fields=None,
                 api_keys=None):
        self.start_index = start_index
        self.max_results = max_results
        self.video_fields = video_fields
        self.api_keys = api_keys if api_keys is not None else {}
        self._loaded = False

        self.item_count = 0
        self._response = None

    # Act as a generator
    def __iter__(self):
        return self

    # Act as a generator
    def next(self):
        if (self.max_results is not None and
            self.item_count >= self.max_results):
            raise StopIteration

        if self._response is None:
            self._next_page()
            #: We could check _loaded first, but why bother?
            self.load()

        try:
            video = self._page_videos_iter.next()
        except StopIteration:
            # We're done with this page.
            if (self._page_videos_count == 0 or
                self._page_videos_count < self.per_page):
                # If the page was either completely empty or not full, reraise
                # the StopIteration.
                raise

            # Try the next page.
            self._response = None
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
        self._page_videos_count = 0
        for item in items:
            data = self.get_item_data(item)
            video = Video(data['link'], fields=self.video_fields,
                          api_keys=self.api_keys)

            video._apply(data)
            self._page_videos_count += 1
            yield video
            if (max_results is not None and
                self._page_videos_count >= max_results):
                break

    def load(self):
        """
        Loads a response if one is not already loaded and tries to extract
        data from it with :meth:`data_from_response`.

        """
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
        """Returns an iterable of unparsed items for the response."""
        raise NotImplementedError

    def get_item_data(self, item):
        """
        Parses a single item for the feed and returns a data dictionary for
        populating a :class:`Video` instance. By default, returns an empty
        dictionary.

        """
        return {}

    def get_page_url(self, page_start, page_max):
        """
        Builds and returns a url for a page of the source by putting the
        results of :meth:`get_page_url_data` into :attr:`page_url_format`.

        """
        if self.page_url_format is None:
            raise NotImplementedError
        format_data = self.get_page_url_data(page_start, page_max)
        return self.page_url_format.format(**format_data)

    def get_page_url_data(self, page_start, page_max):
        """
        Returns a dictionary which will be combined with
        :attr:`page_url_format` to build a page url.

        """
        data = {
            'page_start': page_start,
            'page_max': page_max
        }
        if self.per_page is not None:
            data['page'] = int(math.ceil(float(page_start) / self.per_page))
        return data

    def get_page(self, page_start, page_max):
        """
        Given a start and maximum size for a page, fetches and returns a
        response for that page. The response could be a feedparser dict, a
        parsed json response, or even just an html page.

        """
        raise NotImplementedError

    def data_from_response(self, response):
        """
        Given a response as returned from :meth:`get_page`, returns a
        dictionary of metadata about this iterator. By default, returns an
        empty dictionary.

        """
        return {}


class FeedparserVideoIteratorMixin(object):
    """
    Overrides the :meth:`get_page`, :meth:`data_from_response` and
    :meth:`get_response_items` to use :mod:`feedparser`. :meth:`get_item_data`
    must still be implemented by subclasses.

    """
    def get_page(self, page_start, page_max):
        url = self.get_page_url(page_start, page_max)
        response = feedparser.parse(url,
                                    etag=self.etag,
                                    modified=self.last_modified)
        # Don't let feedparser silence connection problems.
        if isinstance(response.get('bozo_exception', None), urllib2.URLError):
            raise response.bozo_exception
        return response

    def data_from_response(self, response):
        feed = response.feed
        data = {
            'title': feed.get('title'),
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

        # If there are more entries than page length, don't guess.
        if self.per_page is None or len(response.entries) < self.per_page:
            data['video_count'] = len(response.entries)

        return data

    def get_response_items(self, response):
        return response.entries


class VideoFeed(BaseVideoIterator):
    """
    Represents a list of videos which can be found at a certain url. The
    source could easily be an RSS feed, an API response, or a video list page.

    In addition to the parameters for :class:`BaseVideoIterator`, this class
    takes the following arguments:

    :param url: A url representing a feed page.
    :param last_modified: The last known modification date for the feed. This
                          can be sent to the service provider to try to
                          short-circuit fetching and/or loading a feed whose
                          contents are already known.
    :param etag: An etag which can be sent to the service provider to try to
                 short-circuit fetching a feed whose contents are already
                 known.

                 .. seealso:: http://en.wikipedia.org/wiki/HTTP_ETag
    :raises: :exc:`UnhandledURL` if the url can't be handled by the class
             being instantiated.

    :class:`VideoFeed` also supports the following "fields", which are
    populated with :meth:`data_from_response`. Fields which have not been
    populated will be ``None``.

    .. attr:: video_count
        The estimated number of videos for the feed.

    .. attr:: last_modified
        A python datetime representing when the feed was last changed. Before
        loading the feed, this will be equal to the ``last_modified`` date the
        :class:`VideoFeed` was instantiated with.

    .. attr:: etag
        A marker representing a feed's current state. Before loading the feed,
        this will be equal to the ``etag`` the :class:`VideoFeed` was
        instantiated with.

    .. attribute:: description

       A description of the feed.

    .. attribute:: webpage

       The url for an html, human-readable version of the feed.

    .. attribute:: title

       The title of the feed.

    .. attribute:: thumbnail_url

       A URL for a thumbnail representing the whole feed.

    .. attribute:: guid

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

        :raises: :exc:`UnhandledURL` if the url isn't handled by this feed.

        """
        raise UnhandledURL

    def get_page_url_data(self, page_start, page_max):
        data = super(VideoFeed, self).get_page_url_data(page_start, page_max)
        data.update(self.url_data)
        return data


class FeedparserVideoFeed(FeedparserVideoIteratorMixin, VideoFeed):
    pass


class VideoSearch(BaseVideoIterator):
    """
    Represents a search on a video site. In addition to the parameters for
    :class:`BaseVideoIterator`, this class takes the following arguments:

    :param query: The raw string for the search.
    :param order_by: The ordering to apply to the search results. If a suite
                     does not support the given ordering, it will return an
                     empty list. Possible values: ``relevant``, ``latest``,
                     ``popular``, ``None`` (use the default ordering of the
                     suite's service provider). Values may be prefixed with a
                     "-" to indicate descending ordering. Default: ``None``.

    :class:`VideoSearch` also supports the following "fields", which are
    populated with :meth:`data_from_response`. Fields which have not been
    populated will be ``None``.

    .. attr:: video_count
        The estimated number of total videos for this search.

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

    def get_page_url_data(self, page_start, page_max):
        data = super(VideoSearch, self).get_page_url_data(page_start,
                                                          page_max)
        data.update({
            'query': urllib.quote_plus(self.query),
            'order_by': self.order_by
        })
        return data


class FeedparserVideoSearch(FeedparserVideoIteratorMixin, VideoSearch):
    pass
