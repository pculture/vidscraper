__version__ = (1, 0, 2)


from vidscraper.suites import registry


def auto_scrape(url, fields=None, api_keys=None):
    """
    Returns a :class:`.Video` instance with data loaded.

    :param url: A video URL. Video website URLs generally work; more
                obscure urls (like API urls) might work as well.
    :param fields: A list of fields to be fetched for the video. Limiting this
                   may decrease the number of HTTP requests required for
                   loading the video.

                   .. seealso:: :ref:`video-fields`
    :param api_keys: A dictionary of API keys for various services. Check the
                     documentation for each :mod:`suite <vidscraper.suites>`
                     to find what API keys they may want or require.
    :raises: :exc:`.UnhandledVideo` if no :mod:`suite <vidscraper.suites>`
             can be found which handles the video.

    """
    video = registry.get_video(url, fields=fields, api_keys=api_keys)
    video.load()
    return video


auto_feed = registry.get_feed
auto_search = registry.get_searches
handles_video = registry.handles_video
handles_feed = registry.handles_feed
