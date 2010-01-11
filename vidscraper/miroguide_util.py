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

import re

from vidscraper import filetypes


def to_utf8(feedparser_string):
    if str is None:
        return None
    elif isinstance(feedparser_string, str):
        try:
            decoded = feedparser_string.decode('utf-8')
        except UnicodeError:
            try:
                decoded = feedparser_string.decode('latin-1')
            except UnicodeError:
                decoded = feedparser_string.decode('utf-8', 'ignore')
        return decoded.encode('utf-8')
    elif isinstance(feedparser_string, unicode):
        return feedparser_string.encode('utf-8')


def has_video_type(enclosure):
    try:
        type = enclosure['type']
    except KeyError:
        return False
    application_video_mime_types = [
        "application/ogg", 
        "application/x-annodex",
        "application/x-bittorrent", 
        "application/x-shockwave-flash"
    ]
    return (type.startswith('video/') or type.startswith('audio/') or
            type in application_video_mime_types)


def get_first_video_enclosure(entry):
    """Find the first video enclosure in a feedparser entry.  Returns the
    enclosure, or None if no video enclosure is found.
    """

    enclosures = entry.get('media_content') or entry.get('enclosures')
    if not enclosures:
        return None
    best_enclosure = None
    for enclosure in enclosures:
        if has_video_type(enclosure) or \
                filetypes.isAllowedFilename(enclosure.get('url', '')):
            if enclosure.get('isdefault'):
                return enclosure
            elif best_enclosure is None:
                best_enclosure = enclosure
    return best_enclosure


def get_thumbnail_url(entry):
    """Get the URL for a thumbnail from a feedparser entry."""
    # Try the video enclosure
    def _get(d):
        if 'thumbnail' in d:
            if hasattr(d['thumbnail'], 'get') and  d['thumbnail'].get(
                'url') is not None:
                return to_utf8(d['thumbnail']['url'])
            else:
                return to_utf8(d['thumbnail'])
        if 'media:thumbnail' in d:
            return to_utf8(d['media:thumbnail'])
        raise KeyError
    video_enclosure = get_first_video_enclosure(entry)
    if video_enclosure is not None:
        try:
            return _get(video_enclosure)
        except KeyError:
            pass
    # Try to get any enclosure thumbnail
    if 'enclosures' in entry:
        for enclosure in entry.enclosures:
            try:
                return _get(enclosure)
            except KeyError:
                pass
        # Try to get the thumbnail for our entry
    try:
        return _get(entry)
    except KeyError:
        pass

    if entry.get('link', '').find(u'youtube.com') != -1:
        match = re.search(r'<img alt="" src="([^"]+)" />',
                          entry['summary'])
        if match:
            return match.group(1)

    return None
