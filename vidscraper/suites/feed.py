from vidscraper.errors import CantIdentifyUrl
from vidscraper.suites import BaseSuite, registry
from vidscraper.utils.feedparser import (get_first_accepted_enclosure,
                                         get_entry_thumbnail_url,
                                         struct_time_to_datetime)

class FeedSuite(BaseSuite):

    def handles_video_url(self, url):
        return True

    def handles_feed_url(self, url):
        return True

    def get_feed_response(self, feed, url):
        response = super(FeedSuite, self).get_feed_response(feed, url)
        if response.entries or not response.bozo_exception: # good feed
            return response
        raise CantIdentifyUrl

    def parse_feed_entry(self, entry):
        enclosure = get_first_accepted_enclosure(entry)
        if 'published_parsed' in entry:
            best_date = struct_time_to_datetime(entry['published_parsed'])
        elif 'updated_parsed' in entry:
            best_date = struct_time_to_datetime(entry['updated_parsed'])
        else:
            best_date = None

        return {
            'link': entry['link'],
            'title': entry['title'],
            'description': entry['summary'],
            'thumbnail_url': get_entry_thumbnail_url(entry),
            'file_url': enclosure.get('url') if enclosure else None,
            'file_url_mimetype': enclosure.get('type') if enclosure else None,
            'file_url_length': enclosure.get('length') if enclosure else None,
            'publish_datetime': best_date,
            }

registry.register_fallback(FeedSuite)
