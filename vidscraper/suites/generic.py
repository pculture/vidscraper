from vidscraper.suites import BaseSuite, registry
from vidscraper.utils.html import convert_entities
from vidscraper.utils.feedparser import (get_accepted_enclosures,
                                         get_entry_thumbnail_url,
                                         struct_time_to_datetime)
from vidscraper.videos import FeedparserFeed, VideoFile


class Feed(FeedparserFeed):
    """
    Generically handles some of the crazy things we've seen out there. Doesn't
    currently handle multi-page feeds.

    """
    page_url_format = "{url}"
    def get_url_data(self, url):
        return {'url': url}

    def _next_page(self):
        if self.start_index != 1 or self.item_count > 0:
            raise StopIteration
        super(Feed, self)._next_page()

    def get_video_data(self, item):
        if item.get('published_parsed'):
            best_date = struct_time_to_datetime(item['published_parsed'])
        elif item.get('updated_parsed'):
            best_date = struct_time_to_datetime(item['updated_parsed'])
        else:
            best_date = None

        link = item.get('link')
        if 'links' in item:
            for possible_link in item.links:
                if possible_link.get('rel') == 'via':
                    # original URL
                    link = possible_link['href']
                    break
        if ('content' in item and item['content'] and
            item['content'][0]['value']): # Atom
            description = item['content'][0]['value']
        else:
            description = item.get('summary', '')

        files = [VideoFile(url=enclosure.get('url'),
                           mime_type=enclosure.get('type'),
                           length=(enclosure.get('filesize') or
                                   enclosure.get('length')))
                 for enclosure in get_accepted_enclosures(item)]

        embed_code = None
        if 'media_player' in item:
            player = item['media_player']
            if player.get('content'):
                embed_code = convert_entities(player['content'])
            elif 'url' in player:
                files.append(VideoFile(
                                     url=player['url'],
                                     mime_type=player.get('type')))
        if not files:
            files = None
        if 'media_license' in item:
            license = item['media_license']['href']
        else:
            license = item.get('license')
        return {
            'link': link,
            'title': convert_entities(item.get('title', '')),
            'description': description,
            'thumbnail_url': get_entry_thumbnail_url(item),
            'files': files,
            'publish_datetime': best_date,
            'guid': item.get('id'),
            'embed_code': embed_code,
            'tags': [tag['term'] for tag in item['tags']
                     if tag['scheme'] is None] if 'tags' in item else None,
            'license': license
        }


class Suite(BaseSuite):
    feed_class = Feed


registry.register_fallback(Suite)
