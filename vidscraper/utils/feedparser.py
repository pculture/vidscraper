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


def _is_accepted_enclosure(enclosure):
    return (is_accepted_type(enclosure.get('type', '')) or
            is_accepted_filename(enclosure.get('url', '')))


def get_entry_enclosures(entry):
    """
    Returns a list of either media_content or enclosures for the entry.

    The enclosures (or media_content) are only returned if they are non-empty
    and contain a non-empty first item.

    """
    media_content = entry.get('media_content')
    if media_content and media_content[0]:
        return media_content
    enclosures = entry.get('enclosures')
    if enclosures and enclosures[0]:
        return enclosures
    return []


def get_accepted_enclosures(entry):
    """
    Returns a list of either media_content or enclosure items with accepted
    mime types for the entry.

    """
    return filter(_is_accepted_enclosure, get_entry_enclosures(entry))


def get_default_enclosure(enclosures):
    for enclosure in enclosures:
        if enclosure.get('isdefault'):
            return enclosure
    return None


def get_item_thumbnail_url(item):
    """Returns the thumbnail for an enclosure or feedparser entry or raises a
    :exc:`KeyError` if none is found."""
    if 'media_thumbnail' in item:
        return item['media_thumbnail'][0]['url']
    blip_thumbnail_src = item.get('blip_thumbnail_src', None)
    if blip_thumbnail_src:
        return u'http://a.images.blip.tv/{0}'.format(blip_thumbnail_src)
    if 'itunes_image' in item:
        return item['itunes_image']['href']
    if 'image' in item:
        return item['image']['href']
    raise KeyError


def get_entry_thumbnail_url(entry):
    """
    Returns the URL for a thumbnail from a feedparser entry, or ``None`` if
    no thumbnail is found. First tries to return the thumbnail for the default
    enclosure, then for any enclosure, then for the entry in general. If these
    all fail and the entry is from youtube, the content of the entry will be
    searched for an image to use as the thumbnail.

    """
    enclosures = get_accepted_enclosures(entry)

    # Try the default enclosure's thumbnail.
    default_enclosure = get_default_enclosure(enclosures)
    if default_enclosure is not None:
        try:
            return get_item_thumbnail_url(default_enclosure)
        except KeyError:
            pass

    # Try to get any enclosure thumbnail
    for enclosure in enclosures:
        if enclosure is not default_enclosure:
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
