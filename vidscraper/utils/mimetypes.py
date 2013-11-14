"""
Utilities for checking whether file mimetypes are accepted by vidscraper.
Although the name is vidscraper, the library also accepts audio files.

"""

#: A tuple of extensions which :mod:`vidscraper` accepts.
ACCEPTED_EXTENSIONS = (
    '.mov', '.wmv', '.mp4', '.m4v', '.ogg', '.ogv', '.anx',
    '.mpg', '.avi', '.flv', '.mpeg', '.divx', '.xvid', '.rmvb',
    '.mkv', '.m2v', '.ogm'
)


#: A tuple of mimetype prefixes which :mod:`vidscraper` considers generally
#: acceptable.
ACCEPTED_MIMETYPE_PREFIXES = ('video/', 'audio/')


#: A tuple of the various application/* mimetypes which :mod:`vidscraper`
#: explicitly supports.
ACCEPTED_APPLICATION_MIMETYPES = (
    "application/ogg",
    "application/x-annodex",
    "application/x-bittorrent",
    "application/x-shockwave-flash"
)


def is_accepted_filename(filename):
    """
    Returns ``True`` if the ``filename`` ends with an extension from
    :data:`ACCEPTED_EXTENSIONS` and ``False`` otherwise.

    """
    # TODO: Replace this with a simple ``in`` check
    filename = filename.lower()
    for ext in ACCEPTED_EXTENSIONS:
        if filename.endswith(ext):
            return True
    return False


def is_accepted_type(mimetype):
    """
    Returns ``True`` if the mimetype starts with one of the
    :data:`ACCEPTED_MIMETYPE_PREFIXES` or is an
    :data:`ACCEPTED_APPLICATION_MIMETYPE`.

    """
    return (
        any((mimetype.startswith(prefix) for prefix in 
            ACCEPTED_MIMETYPE_PREFIXES)) or
        mimetype in ACCEPTED_APPLICATION_MIMETYPES
    )
