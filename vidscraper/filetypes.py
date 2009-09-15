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

import os

VIDEO_EXTENSIONS = ['.mov', '.wmv', '.mp4', '.m4v', '.ogg', '.anx', '.mpg', '.avi', '.flv', '.mpeg', '.divx', '.xvid', '.rmvb', '.mkv', '.m2v', '.ogm']
AUDIO_EXTENSIONS = ['.mp3', '.m4a', '.wma', '.mka']

MIMETYPES_EXT_MAP = {
    'video/quicktime':  ['.mov'],
    'video/mpeg':       ['.mpeg', '.mpg', '.m2v'],
    'video/mp4':        ['.mp4', '.m4v'],
    'video/flv':        ['.flv'],
    'video/x-flv':      ['.flv'],
    'video/x-ms-wmv':   ['.wmv'],
    'video/x-msvideo':  ['.avi'],
    'video/x-matroska': ['.mkv'],
    'application/ogg':  ['.ogg'],

    'audio/mpeg':       ['.mp3'],
    'audio/mp4':        ['.m4a'],
    'audio/x-ms-wma':   ['.wma'],
    'audio/x-matroska': ['.mka'],
    
    'application/x-bittorrent': ['.torrent']
}

EXT_MIMETYPES_MAP = {}
for (mimetype, exts) in MIMETYPES_EXT_MAP.iteritems():
    for ext in exts:
        if ext not in EXT_MIMETYPES_MAP:
            EXT_MIMETYPES_MAP[ext] = list()
        EXT_MIMETYPES_MAP[ext].append(mimetype)

def isAllowedFilename(filename):
    """
    Pass a filename to this method and it will return a boolean
    saying if the filename represents video, audio or torrent.
    """
    return isVideoFilename(filename) or isAudioFilename(filename) or isTorrentFilename(filename)

def isVideoFilename(filename):
    """
    Pass a filename to this method and it will return a boolean
    saying if the filename represents a video file.
    """
    filename = filename.lower()
    for ext in VIDEO_EXTENSIONS:
        if filename.endswith(ext):
            return True
    return False

def isAudioFilename(filename):
    """
    Pass a filename to this method and it will return a boolean
    saying if the filename represents an audio file.
    """
    filename = filename.lower()
    for ext in AUDIO_EXTENSIONS:
        if filename.endswith(ext):
            return True
    return False

def isTorrentFilename(filename):
    """
    Pass a filename to this method and it will return a boolean
    saying if the filename represents a torrent file.
    """
    filename = filename.lower()
    return filename.endswith('.torrent')

def isVideoEnclosure(enclosure):
    """
    Pass an enclosure dictionary to this method and it will return a boolean
    saying if the enclosure is a video or not.
    """
    return (_hasVideoType(enclosure) or
            _hasVideoExtension(enclosure, 'url') or
            _hasVideoExtension(enclosure, 'href'))

def _hasVideoType(enclosure):
    return ('type' in enclosure and
            (enclosure['type'].startswith(u'video/') or
             enclosure['type'].startswith(u'audio/') or
             enclosure['type'] == u"application/ogg" or
             enclosure['type'] == u"application/x-annodex" or
             enclosure['type'] == u"application/x-bittorrent" or
             enclosure['type'] == u"application/x-shockwave-flash"))

def _hasVideoExtension(enclosure, key):
    from miro import download_utils
    if key in enclosure:
        elems = download_utils.parseURL(enclosure[key], split_path=True)
        return isAllowedFilename(elems[3])
    return False

def isFeedContentType(contentType):
    """Is a content-type for a RSS feed?"""

    feedTypes = [ u'application/rdf+xml', u'application/atom+xml',
            u'application/rss+xml', u'application/podcast+xml', u'text/xml',
            u'application/xml', 
        ]
    for type in feedTypes:
        if contentType.startswith(type):
            return True
    return False

def guessExtension(mimetype):
    """
    Pass a mime type to this method and it will return a corresponding file
    extension, or None if it doesn't know about the type.
    """
    possibleExtensions = MIMETYPES_EXT_MAP.get(mimetype)
    if possibleExtensions is None:
        return None
    return possibleExtensions[0]

def guessMimeType(filename):
    """
    Pass a filename to this method and it will return a corresponding mime type,
    or 'video/unknown' if the filename has a known video extension but no 
    corresponding mime type, or None if it doesn't know about the file extension.
    """
    root, ext = os.path.splitext(filename)
    possibleTypes = EXT_MIMETYPES_MAP.get(ext)
    if possibleTypes is None:
        if isVideoFilename(filename):
            return 'video/unknown'
        elif isAudioFilename(filename):
            return 'audio/unknown'
        else:
            return None
    return possibleTypes[0]
