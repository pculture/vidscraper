import datetime
import math
import re

import feedparser
import simplejson

from vidscraper.util import open_url_while_lying_about_agent

USERNAME_RE = re.compile(r'http://(www\.)?vimeo\.com/'
                         r'(?P<name>((channels|groups)/)?\w+)'
                         r'(/(?P<type>(videos|likes)))?')

_cached_video_count = {}

def _post_url(username, type, query=None):
    if 'channels/' in username:
        username = username.replace('channels/', 'channel/')
    return 'http://vimeo.com/api/v2/%s/%s.json%s' % (username, type,
                                                     query and '?%s' % query or
                                                     '')

def video_count(parsed_feed):
    if not parsed_feed.feed.get('generator', '').endswith('Vimeo'):
        return None
    match = USERNAME_RE.search(parsed_feed.feed.link)
    username = match.group('name')
    url = _post_url(username, 'info')
    json_data = simplejson.load(open_url_while_lying_about_agent(url))
    count = None
    if match.group('type') in ('videos', None):
        if 'total_videos_uploaded' in json_data:
            count = json_data['total_videos_uploaded']
        elif 'total_videos' in json_data:
            count = json_data['total_videos']
    elif match.group('type') == 'likes':
        count = json_data.get('total_videos_liked')
    _cached_video_count[parsed_feed.feed.link] = count
    return count


def bulk_import(parsed_feed):
    match = USERNAME_RE.search(parsed_feed.feed.link)
    username = match.group('name')
    if parsed_feed.feed.link in _cached_video_count:
        count = _cached_video_count[parsed_feed.feed.link]
    else:
        count = video_count(parsed_feed)
    post_url = _post_url(username, match.group('type') or 'videos', 'page=%i')
    parsed_feed = feedparser.FeedParserDict(parsed_feed.copy())
    parsed_feed.entries = []
    for i in range(1, int(math.ceil(count / 20.0)) + 1):
        response = open_url_while_lying_about_agent(post_url % i)
        if response.getcode() != 200:
            break
        data = response.read()
        if not data:
            break
        json_data = simplejson.loads(data)
        for video in json_data:
            parsed_feed.entries.append(feedparser_dict(
                    _json_to_feedparser(video)))

    # clean up cache
    if parsed_feed.feed.link in _cached_video_count:
        del _cached_video_count[parsed_feed.feed.link]

    return parsed_feed

def feedparser_dict(obj):
    if isinstance(obj, dict):
        return feedparser.FeedParserDict(dict(
                [(key, feedparser_dict(value))
                 for (key, value) in obj.items()]))
    if isinstance(obj, (list, tuple)):
        return [feedparser_dict(member) for member in obj]
    return obj

def safe_decode(str_or_unicode):
    if isinstance(str_or_unicode, unicode):
        return str_or_unicode
    else:
        return str_or_unicode.decode('utf8')

def _json_to_feedparser(json):
    upload_date = datetime.datetime.strptime(
        json['upload_date'],
        '%Y-%m-%d %H:%M:%S')
    tags = [{'label': u'Tags',
             'scheme': None,
             'term': safe_decode(json['tags'])}]
    tags.extend({'label': None,
                 'scheme': u'http://vimeo/tag:%s' % tag,
                 'term': tag}
                for tag in safe_decode(json['tags']).split(', '))
    return {
        'author': safe_decode(json['user_name']),
        'enclosures': [
            {'href': u'http://vimeo.com/moogaloop.swf?clip_id=%s' % json['id'],
             'type': u'application/x-shockwave-flash'},
            {'thumbnail': {'width': u'200', 'height': u'150',
                           'url': safe_decode(json['thumbnail_medium']),
                           }}],
        'guidislink': False,
        'id': safe_decode(upload_date.strftime(
                'tag:vimeo,%%Y-%%m-%%d:clip%s' % json['id'].encode('utf8'))),
        'link': safe_decode(json['url']),
        'links': [{'href': safe_decode(json['url']),
                   'rel': 'alternate',
                   'type': 'text/html'}],
        'media:thumbnail': u'',
        'media_credit': safe_decode(json['user_name']),
        'media_player': u'',
        'summary': (u'<p><a href="%(url)s" title="%(title)s">'
                    u'<img src="%(thumbnail_medium)s" alt="%(title)s" /></a>'
                    u'</p><p>%(description)s</p>' % json),
        'summary_detail': {
            'base': u'%s/videos/rss' % safe_decode(json['user_url']),
            'language': None,
            'type': 'text/html',
            'value': (u'<p><a href="%(url)s" title="%(title)s">'
                      u'<img src="%(thumbnail_medium)s" alt="%(title)s" /></a>'
                      u'</p><p>%(description)s</p>' % json),
            },
        'tags': tags,
        'title': safe_decode(json['title']),
        'title_detail': {
            'base': u'%s/videos/rss' % safe_decode(json['user_url']),
            'language': None,
            'type': 'text/plain',
            'value': safe_decode(json['title'])},
        'updated': safe_decode(
            upload_date.strftime('%a, %d %b %Y %H:%M:%S %z')),
        'updated_parsed': upload_date.timetuple()}
