Main Interface
==============

The 5 functions given here should handle most use cases.

.. autofunction:: vidscraper.auto_scrape

.. autofunction:: vidscraper.auto_feed

.. autofunction:: vidscraper.auto_search

.. function:: vidscraper.handles_video

    Returns ``True`` if any registered suite can make a video with the
    given parameters, and ``False`` otherwise.

    .. note:: This does all the work of creating a video, then discards
              it. If you are going to use a video instance if one is
              created, it would be more efficient to use
              :func:`.auto_scrape` directly.

.. function:: vidscraper.handles_feed

    Returns ``True`` if any registered suite can make a feed with the
    given parameters, and ``False`` otherwise.

    .. note:: This does all the work of creating a feed, then discards
              it. If you are going to use a feed instance if one is
              created, it would be more efficient to use
              :func:`.auto_feed` directly.
