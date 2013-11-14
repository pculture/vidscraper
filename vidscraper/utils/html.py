import re

from bs4.dammit import EntitySubstitution


HTML_ENTITY_TO_CHARACTER = EntitySubstitution.HTML_ENTITY_TO_CHARACTER
HTML_ENTITY_TO_CHARACTER_RE = re.compile("|".join(("&{entity};"
                                                   "".format(entity=entity)
                                                   for entity in
                                                   HTML_ENTITY_TO_CHARACTER)))


def _substitute_character(matchobj):
    character = HTML_ENTITY_TO_CHARACTER.get(matchobj.group(0)[1:-1])
    return character


def convert_entities(text):
    """
    Converts HTML entities from the given code to the appropriate characters.
    """
    return unicode(HTML_ENTITY_TO_CHARACTER_RE.sub(_substitute_character,
                                                   text))
