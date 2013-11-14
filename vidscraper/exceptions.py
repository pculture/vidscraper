class VidscraperError(Exception):
    """Base error for :mod:`vidscraper`."""
    pass


class UnhandledVideo(VidscraperError):
    """
    Raised by :class:`.VideoLoader`\ s and :doc:`suites </api/suites>` if a
    given video can't be handled.

    """
    pass


class UnhandledFeed(VidscraperError):
    """
    Raised if a feed can't be handled by a :doc:`suite </api/suites>` or
    :class:`.BaseFeed` subclass.

    """
    pass


class UnhandledSearch(VidscraperError):
    """
    Raised if a search can't be handled by a :doc:`suite </api/suites>` or
    :class:`.BaseSearch` subclass.

    """
    pass


class InvalidVideo(VidscraperError):
    """
    Raised if a video is found to be invalid in some way after data has
    been collected on it.

    """
    pass


class VideoDeleted(VidscraperError):
    """Raised if the remote server has deleted the video being scraped."""
    pass
