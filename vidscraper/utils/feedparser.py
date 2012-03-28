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

import datetime
import re

from vidscraper.utils.mimetypes import is_accepted_filename, is_accepted_type


def struct_time_to_datetime(struct_time):
    """
    Returns a python datetime for the passed-in ``struct_time``.

    """
    return datetime.datetime(*struct_time[:6])


def get_entry_enclosures(entry):
    """Returns a list of enclosures or media_content for the entry."""
    return entry.get('media_content') or entry.get('enclosures') or []


def get_first_accepted_enclosure(entry):
    """
    Returns the first accepted enclosure in a feedparser entry, or ``None`` if
    no such enclosure is found. An enclosure is accepted if it contains a file
    which passes the :func:`.is_accepted_filename` or :func:`.is_accepted_type`
    checks.

    """
    enclosures = get_entry_enclosures(entry)
    if not enclosures:
        return None
    best_enclosure = None
    for enclosure in enclosures:
        if (is_accepted_type(enclosure.get('type', '')) or
                is_accepted_filename(enclosure.get('url', ''))):
            if enclosure.get('isdefault'):
                return enclosure
            elif best_enclosure is None:
                best_enclosure = enclosure
    return best_enclosure


def get_item_thumbnail_url(item):
    """Returns the thumbnail for an enclosure or feedparser entry or raises a
    :exc:`KeyError` if none is found."""
    if 'media_thumbnail' in item:
        return item['media_thumbnail'][0]['url']
    blip_thumbnail_src = item.get('blip_thumbnail_src', None)
    if blip_thumbnail_src:
        return u'http://a.images.blip.tv/%s' % blip_thumbnail_src
    if 'itunes_image' in item:
        return item['itunes_image']['href']
    if 'image' in item:
        return item['image']['href']
    raise KeyError


def get_entry_thumbnail_url(entry):
    """
    Returns the URL for a thumbnail from a feedparser entry, or ``None`` if
    no thumbnail is found. First tries to return a video thumbnail, then any
    enclosure thumbnail, then the general entry thumbnail. If these all fail and
    the entry is from youtube, the content of the entry will be searched for an
    image to use as the thumbnail.

    """
    # Try the video enclosure's thumbnail
    video_enclosure = get_first_accepted_enclosure(entry)
    if video_enclosure is not None:
        try:
            return get_item_thumbnail_url(video_enclosure)
        except KeyError:
            pass

    # Try to get any enclosure thumbnail
    for enclosure in get_entry_enclosures(entry):
        try:
            return get_item_thumbnail_url(enclosure)
        except KeyError:
            pass

    # Try to get the general thumbnail for the entry
    try:
        return get_item_thumbnail_url(entry)
    except KeyError:
        pass

    # Check the content
    if entry.get('link', '').find(u'youtube.com') != -1:
        if 'content' in entry:
            content = entry['content'][0]['value']
        elif 'summary' in entry:
            content = entry['summary']
        else:
            return None
        match = re.search(r'<img alt="" src="([^"]+)" />',
                          content)
        if match:
            return match.group(1)

    return None
