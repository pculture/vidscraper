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

from datetime import datetime
import itertools
import json
import math
import mimetypes
import operator
import urllib
import urllib2

import feedparser
import requests
try:
    import grequests
except (RuntimeError, ImportError):
    grequests = None

from vidscraper import __version__
from vidscraper.exceptions import (UnhandledVideo, UnhandledFeed,
                                   UnhandledSearch, InvalidVideo)
from vidscraper.utils.feedparser import (get_item_thumbnail_url,
                                         struct_time_to_datetime)
from vidscraper.utils.search import (search_string_from_terms,
                                     terms_from_search_string)


PREFERRED_MIMETYPES = ('video/webm', 'video/ogg', 'video/mp4')
REQUEST_TIMEOUT = 3
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux) Safari/536.10 '
                  'vidscraper/{version}'.format(version=__version__)
}


def _isoformat_to_datetime(dt_str):
    """
    Tries to convert an isoformatted string to a datetime. Raises TypeError
    if the input is not a string or ValueError if it is not isoformatted.

    """
    format = "%Y-%m-%dT%H:%M:%S"
    try:
        return datetime.strptime(dt_str, format)
    except ValueError:
        pass

    # Maybe it has microseconds?
    format = "%Y-%m-%dT%H:%M:%S.%f"
    return datetime.strptime(dt_str, format)


class Video(object):
    """
    This is the class which should be used to represent videos which are
    returned by suite scraping, searching and feed parsing.

    :param url: The "pasted" url for the video.
    :param loaders: An iterable of :class:`VideoLoader` instances that will
                    be used to load video data.
    :param fields: A list of fields which should be fetched for the video.
                   This will be used to optimize the fetching process. Other
                   fields will not populated, even if the data is available.

    """
    # FIELDS
    _all_fields = (
        'title', 'description', 'publish_datetime', 'flash_enclosure_url',
        'is_embeddable', 'embed_code', 'thumbnail_url', 'user', 'user_url',
        'tags', 'link', 'guid', 'license', 'files',
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
    #: A list of :class:`VideoFile` instances representing all the possible
    #: files for this video.
    files = None
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

    def __init__(self, url, loaders=None, fields=None):
        if fields is None:
            self.fields = list(self._all_fields)
        else:
            self.fields = [f for f in fields if f in self._all_fields]
        self.url = url
        self.loaders = loaders if loaders is not None else []
        self._errors = {}

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

    def load(self):
        """
        If the video hasn't been loaded before, runs the loaders and populates
        the video's :attr:`fields`.

        """
        if not self._loaded:
            data = self.run_loaders()
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

    def get_best_loaders(self):
        """
        Returns a list of loaders from :attr:`loaders` which can be used in
        combination to fill all missing fields - or as many of them as
        possible.

        This will prefer the first listed loaders and will prefer small
        combinations of loaders, so that the smallest number of smallest
        possible responses will be fetched.

        """
        missing_fields = set(self.missing_fields)
        # Our initial state is that we cover none of the missing fields, and
        # that we use none of the available loaders.
        min_remaining = len(missing_fields)
        best_loaders = []

        # Loop through all combinations of any size that can be made with the
        # available loaders.
        for size in xrange(1, len(self.loaders) + 1):
            for loaders in itertools.combinations(self.loaders, size):
                # First, build a set of the fields that are provided by the
                # loaders.
                field_set = reduce(operator.or_, (l.fields for l in loaders))
                remaining = len(missing_fields - field_set)

                # If these loaders fill all the missing fields, take them
                # immediately.
                if not remaining:
                    return loaders

                # Otherwise, note the loaders iff they would decrease the 
                # number of missing fields.
                if remaining < min_remaining:
                    best_loaders = loaders
                    min_remaining = remaining
        return best_loaders

    def run_loaders(self):
        """
        Runs :meth:`get_best_loaders` and then gets data from each loader.

        """
        best_loaders = self.get_best_loaders()

        if grequests is None:
            responses = [requests.get(loader.get_url(),
                                      **loader.get_request_kwargs())
                         for loader in best_loaders]
        else:
            responses = grequests.map(
                                 [grequests.get(loader.get_url(),
                                                **loader.get_request_kwargs())
                                  for loader in best_loaders])

        data = {}
        for loader, response in itertools.izip(best_loaders, responses):
            try:
                data.update(loader.get_video_data(response))
            except Exception, exc:
                self._errors[loader] = exc

        return data

    def items(self):
        """Iterator over (field, value) for requested fields."""
        for field in self.fields:
            yield (field, getattr(self, field))

    def serialize(self):
        """
        Serializes the video as a python dictionary containing the original
        url and fields used to initialize the video, as well as the value of
        each field on the video. Since loaders are intended to be provided by
        suites and include sensitive information (api keys), they are not
        serialized.

        """
        data = dict(self.items())

        dt = data.get('publish_datetime')
        if isinstance(dt, datetime):
            data['publish_datetime'] = dt.isoformat()

        files = data.get('files')
        if files is not None:
            data['files'] = [f.serialize() for f in files]

        data.update({
            'url': self.url,
            'fields': self.fields
        })
        return data

    @classmethod
    def deserialize(cls, data, api_keys=None):
        """
        Given a data dictionary such as would be provided by :meth:`serialize`
        and, optionally, api keys, constructs a :class:`Video` instance for
        the url and fields in the data, with field values prepopulated from
        the dictionary.

        :param data: A dictionary as would be provided by :meth:`serialize`.
        :param api_keys: ``None``, or a dictionary of API keys to instantiate
                         the deserialized video with.

        """
        from vidscraper.suites import registry
        video = registry.get_video(data['url'],
                                   fields=data['fields'],
                                   api_keys=api_keys,
                                   require_loaders=False)

        dt = data.get('publish_datetime')
        if dt is not None:
            data['publish_datetime'] = _isoformat_to_datetime(dt)

        files = data.get('files')
        if files is not None:
            data['files'] = [VideoFile.deserialize(f) for f in files]

        video._apply(data)
        return video

    def get_file(self, preferred_mimetypes=PREFERRED_MIMETYPES):
        """
        Returns the preferred file from the files for this video. Vidscraper
        prefers open formats and well-compressed formats. If no file mimetypes
        are known, the first file will be returned.

        """
        if not self.files:
            return None

        chosen = self.files[0]
        try:
            chosen_index = PREFERRED_MIMETYPES.index(chosen.mime_type)
        except ValueError:
            chosen_index = None

        for f in self.files[1:]:
            try:
                f_index = PREFERRED_MIMETYPES.index(f.mime_type)
            except ValueError:
                continue
            if chosen_index is None or f_index < chosen_index:
                chosen_index = f_index
                chosen = f

        return chosen


class VideoFile(object):
    """
    Represents a video file hosted somewhere. The only required attribute is
    the file's :attr:`url`. There are also several optional metadata
    attributes, which represent what is claimed about the video by the data
    provider, not necessarily what is actually true about the video.

    """
    #: The URL of this video file.
    url = None
    #: When the URL for this file expires, if at all.
    expires = None
    #: The size of the file, in bytes.
    length = None
    #: The width of the video, in pixels.
    width = None
    #: The height of the video, in pixels.
    height = None
    #: The MIME type of the video.
    mime_type = None

    def __init__(self, url, expires=None, length=None, width=None,
                 height=None, mime_type=None):
        self.url = url
        self.expires = expires
        self.length = length
        self.width = width
        self.height = height
        self.mime_type = (mimetypes.guess_type(url)
                          if mime_type is None else mime_type)

    def __repr__(self):
        return u'<VideoFile: {url}>'.format(url=unicode(self))

    def __unicode__(self):
        if len(self.url) > 17:
            url = self.url[:17] + '...'
        else:
            url = self.url
        return unicode(url)

    def __eq__(self, other):
        if not isinstance(other, VideoFile):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def serialize(self):
        """
        Serializes the :class:`VideoFile` as a python dictionary.

        """
        data = dict(self.__dict__.iteritems())

        dt = data['expires']
        if isinstance(dt, datetime):
            data['expires'] = dt.isoformat()

        return data

    @classmethod
    def deserialize(cls, data):
        """
        Given a data dictionary such as would be provided by
        :meth:`serialize`, constructs a :class:`VideoFile` instance.

        """
        dt = data.get('expires', None)
        if dt is not None:
            data['expires'] = _isoformat_to_datetime(dt)
        return cls(**data)


class VideoLoader(object):
    """
    This is a base class for objects that fetch data for a video, for example
    from an API or a page scrape.

    :param url: The "pasted" url for which data should be loaded.
    :param api_keys: A dictionary of API keys which may be needed to load data
                     with this loader.

    """
    #: A set of fields this loader believes it can provide.
    fields = set()

    #: A format string which, paired with :attr:`url_data`, returns a suitable
    #: url for this loader to fetch data from.
    url_format = None

    #: The number of seconds before this loader times out. See python-requests
    #: documentation for more information.
    timeout = REQUEST_TIMEOUT

    #: Extra headers to set on the requests for this loader. See
    #: python-requests documentation for more information.
    headers = REQUEST_HEADERS

    def __init__(self, url, api_keys=None):
        self.url = url
        self.api_keys = api_keys if api_keys is not None else {}
        self.url_data = self.get_url_data(url)

    def get_url_data(self, url):
        """
        Parses the url into data which can be used to construct a url this
        loader can use to get data.

        :raises: :exc:`.UnhandledVideo` if the url isn't handled by this
                 loader.

        """
        raise UnhandledVideo(url)

    def get_url(self):
        """
        Returns a url which can be fetched to get a response that this loader
        can process into data.

        """
        if self.url_format is None:
            raise NotImplementedError
        return self.url_format.format(**self.url_data)

    def get_headers(self):
        """
        Returns a dictionary of headers which will be added to the request.
        By default, this is a copy of :attr:`headers`.

        """
        return self.headers.copy()

    def get_request_kwargs(self):
        """
        Returns the kwargs used for making an HTTP request for this loader
        (with python-requests).

        """
        return {
            'timeout': self.timeout,
            'headers': self.get_headers(),
        }

    def get_video_data(self, response):
        """
        Parses the given ``response`` and returns a data dictionary for
        populating a :class:`Video` instance. By default, returns an empty
        dictionary.

        """
        return {}


class OEmbedLoaderMixin(object):
    """
    Mixin to provide basic OEmbed functionality. Subclasses need to provide an
    endpoint, define a get_url_data method, and provide a url_format - for the
    video URL, not the oembed API URL.

    This is provided as a mixin rather than a subclass of :class:`VideoLoader`
    so that it can be used on top of any class or mixin that overrides
    :meth:`VideoLoader.get_url`.

    """
    fields = set(('title', 'user', 'user_url', 'thumbnail_url', 'embed_code'))

    #: The endpoint for the OEmbed API.
    endpoint = None

    full_url_format = "{endpoint}?url={url}"

    def get_video_url(self):
        return super(OEmbedLoaderMixin, self).get_url()

    def get_url(self):
        url = self.get_video_url()
        return self.full_url_format.format(url=urllib.quote_plus(url),
                                           endpoint=self.endpoint)

    def get_video_data(self, response):
        parsed = json.loads(response.text)
        data = {
            'title': parsed['title'],
            'user': parsed['author_name'],
            'user_url': parsed['author_url'],
            'thumbnail_url': parsed['thumbnail_url'],
            'embed_code': parsed['html']
        }
        return data


class VideoIterator(object):
    """
    Generic base class for iterating over groups of videos spread across
    multiple urls - for example, an rss feed, an api response, or a video list
    page.

    :param start_index: The index of the first video to return. Default: 1.
    :type start_index: integer >= 1
    :param max_results: The maximum number of videos to return. If this is
                        ``None`` (the default), as many videos as possible
                        will be returned.
    :param video_fields: A list of fields to be fetched for each video in the
                         iterator. Limiting this may decrease the number of
                         HTTP requests required for loading video data.

                         .. seealso:: :ref:`video-fields`
    :param api_keys: A dictionary of API keys for various services. Check the
                     documentation for each :mod:`suite <vidscraper.suites>`
                     to find what API keys they may want or require.

    """
    #: Describes the number of videos expected on each page. This should be
    #: set whether or not the number of videos per page can be controlled.
    per_page = None

    #: A format string which will be used to build page urls for this
    #: iterator. This should use the {} format described under str.format()
    #: in the python docs:
    #: http://docs.python.org/library/stdtypes.html#str.format
    page_url_format = None

    #: The number of seconds before this loader times out. See python-requests
    #: documentation for more information.
    timeout = REQUEST_TIMEOUT

    #: Extra headers to set on the requests for this loader. See
    #: python-requests documentation for more information.
    headers = REQUEST_HEADERS

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
        if self.is_finished():
            raise StopIteration

        if self._response is None:
            self._next_page()
            #: We could check _loaded first, but why bother?
            self.load()

        try:
            video = self._page_videos_iter.next()
        except StopIteration:
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

    def _page_videos(self, response, page_max=None):
        # Avoid circular imports.
        from vidscraper.suites import registry
        items = self.get_response_items(response)
        self._page_videos_count = 0
        for item in items:
            try:
                data = self.get_video_data(item)
            except InvalidVideo:
                continue
            url = data['link']
            video = registry.get_video(url,
                                       fields=self.video_fields,
                                       api_keys=self.api_keys,
                                       require_loaders=False)
            video._apply(data)
            self._page_videos_count += 1
            yield video
            if (page_max is not None and
                self._page_videos_count >= page_max):
                break

    def is_finished(self):
        if (self.max_results is not None and
            self.item_count >= self.max_results):
            return True
        if self._response is None:
            # Then we're between pages.
            try:
                if (self._page_videos_count == 0 or
                    self._page_videos_count < self.per_page):
                    # The last page was either empty or not full.
                    return True
            except AttributeError:
                pass
        return False

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

    def get_video_data(self, item):
        """
        Parses a single item for the feed and returns a data dictionary for
        populating a :class:`Video` instance. By default, returns an empty
        dictionary. Raises :exc:`.InvalidVideo` if the item is found to be
        invalid in some way; this causes the item to be ignored.

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

    def get_headers(self):
        """
        Returns a dictionary of headers which will be added to the request.
        By default, this is a copy of :attr:`headers`.

        """
        return self.headers.copy()

    def get_request_kwargs(self):
        """
        Returns the kwargs used for making an HTTP request for this feed.

        """
        return {
            'timeout': self.timeout,
            'headers': self.get_headers()
        }

    def get_page(self, page_start, page_max):
        """
        Given a start and maximum size for a page, fetches and returns a
        response for that page. The response could be a feedparser dict, a
        parsed json response, or even just an html page.

        """
        page_url = self.get_page_url(page_start, page_max)
        response = requests.get(page_url, **self.get_request_kwargs())
        return response

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
    :meth:`get_response_items` to use :mod:`feedparser`.
    :meth:`get_video_data` must still be implemented by subclasses.

    """
    def get_request_kwargs(self):
        return {
            'etag': getattr(self, 'etag', None),
            'modified': getattr(self, 'last_modified', None),
            'request_headers': self.get_headers()
        }

    def get_page(self, page_start, page_max):
        page_url = self.get_page_url(page_start, page_max)
        response = feedparser.parse(page_url, **self.get_request_kwargs())
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


class BaseFeed(VideoIterator):
    """
    Represents a list of videos which can be found at a certain url. The
    source could easily be an RSS feed, an API response, or a video list page.

    In addition to the parameters for :class:`VideoIterator`, this class
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
    :raises: :exc:`.UnhandledFeed` if the url can't be handled by the class
             being instantiated.

    :class:`BaseFeed` also supports the following "fields", which are
    populated with :meth:`data_from_response`. Fields which have not been
    populated will be ``None``.

    .. attribute:: video_count

        The estimated number of videos for the feed.

    .. attribute:: last_modified

        A python datetime representing when the feed was last changed. Before
        loading the feed, this will be equal to the ``last_modified`` date
        the :class:`BaseFeed` was instantiated with.

    .. attribute:: etag

        A marker representing a feed's current state. Before loading the feed,
        this will be equal to the ``etag`` the :class:`BaseFeed` was
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
        super(BaseFeed, self).__init__(**kwargs)

        self.url = url
        self.url_data = self.get_url_data(url)
        self.last_modified = last_modified
        self.etag = etag

    def get_url_data(self, url):
        """
        Parses the url into data which can be used to construct page urls.

        :raises: :exc:`.UnhandledFeed` if the url isn't handled by this feed.

        """
        raise UnhandledFeed(url)

    def get_page_url_data(self, page_start, page_max):
        data = super(BaseFeed, self).get_page_url_data(page_start, page_max)
        data.update(self.url_data)
        return data


class FeedparserFeed(FeedparserVideoIteratorMixin, BaseFeed):
    pass


class BaseSearch(VideoIterator):
    """
    Represents a search on a video site. In addition to the parameters for
    :class:`VideoIterator`, this class takes the following arguments:

    :param query: The raw string for the search.
    :param order_by: The ordering to apply to the search results. If a suite
                     does not support the given ordering, it will return an
                     empty list. Possible values: ``relevant``, ``latest``,
                     ``popular``. Values may be prefixed with a "-" to
                     indicate descending ordering. Default: ``relevant``.

    :raises: :exc:`.UnhandledSearch` if the class doesn't support the given
             parameters.

    :class:`BaseSearch` also supports the following "fields", which are
    populated with :meth:`data_from_response`. Fields which have not been
    populated will be ``None``.

    .. attribute:: video_count

        The estimated number of total videos for this search.

    """
    _all_fields = ('video_count',)
    video_count = None

    #: Dictionary mapping our order_by options (relevant, latest, and popular)
    #: to the service's equivalent term. If an order_by option is not in this
    #: dictionary, it is assumed not to be supported by the service.
    order_by_map = {
        'relevant': 'relevant'
    }

    def __init__(self, query, order_by='relevant', **kwargs):
        super(BaseSearch, self).__init__(**kwargs)
        # Normalize the search
        self.include_terms, self.exclude_terms = terms_from_search_string(
            query)
        self.query = search_string_from_terms(self.include_terms,
                                              self.exclude_terms)
        self.raw_query = query
        self.order_by = order_by
        if order_by not in self.order_by_map:
            raise UnhandledSearch(u"{0} does not support an ordering called "
                                  u"{1}".format(self.__class__.__name__,
                                                order_by))

    def get_page_url_data(self, page_start, page_max):
        data = super(BaseSearch, self).get_page_url_data(page_start,
                                                          page_max)
        data.update({
            'query': urllib.quote_plus(unicode(self.query).encode('utf-8')),
            'order_by': self.order_by_map[self.order_by]
        })
        return data


class FeedparserSearch(FeedparserVideoIteratorMixin, BaseSearch):
    pass
