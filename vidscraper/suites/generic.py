from vidscraper.suites import BaseSuite, registry
from vidscraper.utils.html import convert_entities
from vidscraper.utils.feedparser import (get_first_accepted_enclosure,
                                         get_entry_thumbnail_url,
                                         struct_time_to_datetime)
from vidscraper.videos import FeedparserVideoFeed, VideoDownload


class GenericFeed(FeedparserVideoFeed):
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
        super(GenericFeed, self)._next_page()

    def get_video_data(self, item):
        enclosure = get_first_accepted_enclosure(item)
        if 'published_parsed' in item:
            best_date = struct_time_to_datetime(item['published_parsed'])
        elif 'updated_parsed' in item:
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

        embed_code = None
        downloads = []
        if enclosure:
            downloads.append(VideoDownload(
                url=enclosure.get('url'),
                mime_type=enclosure.get('type'),
                length=enclosure.get('filesize') or enclosure.get('length')))
        if 'media_player' in item:
            player = item['media_player']
            if player.get('content'):
                embed_code = convert_entities(player['content'])
            elif 'url' in player:
                downloads.append(VideoDownload(
                                     url=player['url'],
                                     mime_type=player.get('type',
                                            'application/x-shockwave-flash')))
        if not downloads:
            downloads = None
        if 'media_license' in item:
            license = item['media_license']['href']
        else:
            license = item.get('license')
        return {
            'link': link,
            'title': convert_entities(item['title']),
            'description': description,
            'thumbnail_url': get_entry_thumbnail_url(item),
            'downloads': downloads,
            'publish_datetime': best_date,
            'guid': item.get('id'),
            'embed_code': embed_code,
            'tags': [tag['term'] for tag in item['tags']
                     if tag['scheme'] is None] if 'tags' in item else None,
            'license': license
        }


class GenericFeedSuite(BaseSuite):
    feed_class = GenericFeed


registry.register_fallback(GenericFeedSuite)
