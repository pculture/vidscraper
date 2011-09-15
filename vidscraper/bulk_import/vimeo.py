import datetime
import math
import re
import urllib

import feedparser
import simplejson
import oauth2

from vidscraper.sites import vimeo
from vidscraper.utils.http import (open_url_while_lying_about_agent,
                             random_exponential_backoff)

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
    parsed_feed = feedparser.FeedParserDict(parsed_feed.copy())
    parsed_feed.entries = []

    consumer = oauth2.Consumer(vimeo.VIMEO_API_KEY, vimeo.VIMEO_API_SECRET)
    client = oauth2.Client(consumer)
    data = {
        'format': 'json',
        'method': 'vimeo.videos.getUploaded',
        'per_page': 50,
        'sort': 'newest',
        'full_response': 'yes',
        'user_id': username
        }
    if username.startswith('channels'):
        del data['user_id']
        data['method'] = 'vimeo.channels.getVideos'
        data['channel_id'] = username.split('/', 1)[1]
    elif username.startswith('groups'):
        del data['user_id']
        data['method'] = 'vimeo.groups.getVideos'
        data['group_id'] = username.split('/', 1)[1]
    elif match.group('type') == 'likes':
        data['method'] = 'vimeo.videos.getLikes'
    
    for i in range(1, int(math.ceil(count / 50.0)) + 1):
        data['page'] = i
        backoff = random_exponential_backoff(2)
        api_data = None
        for j in range(5):
            try:
                api_raw_data = client.request('%s?%s' % (
                        vimeo.VIMEO_API_URL,
                        urllib.urlencode(data)))[1]
                api_data = simplejson.loads(api_raw_data)
                break
            except Exception:
                continue
            else:
                if 'videos' in api_data:
                    break
            backoff.next()
        if api_data is None:
            break
        for video in api_data['videos']['video']:
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
    if 'tags' in json:
        tags = [{'label': tag['normalized'],
                 'scheme': tag['url'],
                 'term': tag['_content']}
                for tag in json['tags']['tag']]
    else:
        tags = []
    id_ = json['id']
    url = json['urls']['url'][0]['_content']
    username = json['owner']['username']
    user_url = json['owner']['profileurl']
    thumbnail = None
    thumbnail_size = (0, 0)
    for d in json['thumbnails']['thumbnail']:
        size = (int(d['width']), int(d['height']))
        if size > thumbnail_size:
            thumbnail, thumbnail_size = d['_content'], size
    
    return {
        'author': safe_decode(username),
        'enclosures': [
            {'href': u'http://vimeo.com/moogaloop.swf?clip_id=%s' % id_,
             'type': u'application/x-shockwave-flash'},
            {'thumbnail': {'width': unicode(thumbnail_size[0]),
                           'height': unicode(thumbnail_size[1]),
                           'url': safe_decode(thumbnail),
                           }}],
        'guidislink': False,
        'id': safe_decode(upload_date.strftime(
                'tag:vimeo,%%Y-%%m-%%d:clip%s' % (
                    unicode(id_).encode('utf8')))),
        'link': safe_decode(url),
        'links': [{'href': safe_decode(url),
                   'rel': 'alternate',
                   'type': 'text/html'}],
        'media:thumbnail': u'',
        'media_credit': safe_decode(username),
        'media_player': u'',
        'summary': (u'<p><a href="%(url)s" title="%(title)s">'
                    u'<img src="%(thumbnail)s" alt="%(title)s" /></a>'
                    u'</p><p>%(description)s</p>' % {
                'title': json['title'],
                'thumbnail': thumbnail,
                'description': json['description'],
                'url': url}),
        'summary_detail': {
            'base': u'%s/videos/rss' % safe_decode(user_url),
            'language': None,
            'type': 'text/html',
            'value': (u'<p><a href="%(url)s" title="%(title)s">'
                      u'<img src="%(thumbnail)s" alt="%(title)s" /></a>'
                      u'</p><p>%(description)s</p>' % {
                    'title': json['title'],
                    'thumbnail': thumbnail,
                    'description': json['description'],
                    'url': url}),
            },
        'tags': tags,
        'title': safe_decode(json['title']),
        'title_detail': {
            'base': u'%s/videos/rss' % safe_decode(user_url),
            'language': None,
            'type': 'text/plain',
            'value': safe_decode(json['title'])},
        'updated': safe_decode(
            upload_date.strftime('%a, %d %b %Y %H:%M:%S %z')),
        'updated_parsed': upload_date.timetuple()}
