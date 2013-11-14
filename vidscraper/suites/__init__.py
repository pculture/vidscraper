from vidscraper.suites.base import registry, BaseSuite

# Force loading of these modules so that the default suites get registered.
from vidscraper.suites import (blip, fora, google, ustream, vimeo, youtube,
                               generic, kaltura)
