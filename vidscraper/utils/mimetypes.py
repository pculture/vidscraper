# Miro - an RSS based video player application
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
