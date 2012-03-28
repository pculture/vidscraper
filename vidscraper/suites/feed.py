from vidscraper.errors import CantIdentifyUrl
from vidscraper.suites import BaseSuite, registry
from vidscraper.utils.html import convert_entities, make_embed_code
from vidscraper.utils.feedparser import (get_first_accepted_enclosure,
                                         get_entry_thumbnail_url,
                                         struct_time_to_datetime)

class GenericFeedSuite(BaseSuite):

    def handles_video_url(self, url):
        return True

    def handles_feed_url(self, url):
        return True

    def get_feed_response(self, feed, url):
        response = super(GenericFeedSuite, self).get_feed_response(feed, url)
        if response.entries or not response.bozo_exception: # good feed
            return response
        if response.bozo_exception:
            raise CantIdentifyUrl('exception during response',
                                  response.bozo_exception)
        else:
            raise CantIdentifyUrl

    def parse_feed_entry(self, entry):
        enclosure = get_first_accepted_enclosure(entry)
        if 'published_parsed' in entry:
            best_date = struct_time_to_datetime(entry['published_parsed'])
        elif 'updated_parsed' in entry:
            best_date = struct_time_to_datetime(entry['updated_parsed'])
        else:
            best_date = None

        link = entry.get('link')
        if 'links' in entry:
            for possible_link in entry.links:
                if possible_link.get('rel') == 'via':
                    # original URL
                    link = possible_link['href']
                    break
        if ('content' in entry and entry['content'] and
            entry['content'][0]['value']): # Atom
            description = entry['content'][0]['value']
        else:
            description = entry.get('summary', '')

        embed_code = None
        if 'media_player' in entry:
            player = entry['media_player']
            if player.get('content'):
                embed_code = convert_entities(player['content'])
            elif 'url' in player:
                embed_code = make_embed_code(player['url'], '')

        return {
            'link': link,
            'title': convert_entities(entry['title']),
            'description': description,
            'thumbnail_url': get_entry_thumbnail_url(entry),
            'file_url': enclosure.get('url') if enclosure else None,
            'file_url_mimetype': enclosure.get('type') if enclosure else None,
            'file_url_length': ((enclosure.get('filesize') or
                                enclosure.get('length'))
                                if enclosure else None),
            'publish_datetime': best_date,
            'guid': entry.get('id'),
            'embed_code': embed_code,
            'tags': [tag['term'] for tag in entry['tags']
                     if tag['scheme'] is None] if 'tags' in entry else None,
            'license': entry.get('license',
                                 entry.get('media_license', {}).get('href'))
            }

registry.register_fallback(GenericFeedSuite)
