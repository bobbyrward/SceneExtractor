import re
from datetime import date


__all__ = [
    'SceneName'
    ]

RELEASE_TYPE_MOVIE = 'Movie'
RELEASE_TYPE_TV = 'TV'
RELEASE_TYPE_EBOOK = 'EBook'
RELEASE_TYPE_UNKNOWN = 'Unknown'

RELEASE_TYPES = [
    RELEASE_TYPE_MOVIE,
    RELEASE_TYPE_TV,
    RELEASE_TYPE_EBOOK,
    RELEASE_TYPE_UNKNOWN,
    ]


# list of valid encoding types
ENCODING_TYPES = [
    'XviD',
    'x264',
    ]


# list of valid movie source types
MOVIE_SOURCE_NAMES = [
    'DVDRip',
    'BDRip',
    'BluRay',
    ]


# list of valid tv source types
TV_SOURCE_NAMES = [
    'DSR',
    'PDTV',
    'HDTV',
    ]


# list of valid ebook source types
EBOOK_SOURCE_NAMES = [
    'EBook',
    ]


# list of other valid tags
VALID_TAGS = [
    'FESTIVAL',
    'STV',
    'LIMITED',
    'TV',
    'READ.NFO',
    'WS',
    'FS',
    'PROPER',
    'REPACK',
    'RERIP',
    'REAL',
    'RETAIL',
    'EXTENDED',
    'REMASTERED',
    'RATED',
    'UNRATED',
    'CHRONO',
    'THEATRICAL',
    'DC',
    'SE',
    'UNCUT',
    'INTERNAL',
    'DUBBED',
    'SUBBED',
    'FINAL',
    'COLORIZED',
    '1080p',
    '720p',
    'RETAiL',
    ]


# regular expression for extractiong a cd number
CD_NUMBER_RE = re.compile('^cd\d+$', re.IGNORECASE)


# regular expression for matching the production year
YEAR_RE = re.compile(
    '^[12]\d{3}$'
    )


# regular expression for matching season and episode numbers
SEASON_EPISODE_RE = re.compile(
    '^S(\d{2,})E(\d{2,})$',
    re.IGNORECASE
    )


# For when an episode name screws up the logic
SEASON_EPISODE_REMAINDER_RE = re.compile(
    '^(.*?)\.S(\d{2,})E(\d{2,})\.(.*?)$',
    re.IGNORECASE
    )


# For when an episode date screws up the logic (With optional episode name)
EPISODE_DATE_REMAINDER_RE = re.compile(
    '^(.*?)\.(\d{4})\.(\d{2})\.(\d{2})(\.(.*?))?$'
    )


# create a function to check for the tag in a specific list
def make_check_tag_function(*tag_lists):
    # find the tag in tag_list or return None
    def check_tag_in_list(tag):
        for tag_list in tag_lists:
            for tag_name in tag_list:
                if tag.lower() == tag_name.lower():
                    return tag_name

        return None

    return check_tag_in_list


check_tag_encoding_type = make_check_tag_function(ENCODING_TYPES)

check_tag_valid_tag = make_check_tag_function(VALID_TAGS)

check_tag_source_type = make_check_tag_function(
        MOVIE_SOURCE_NAMES,
        TV_SOURCE_NAMES,
        EBOOK_SOURCE_NAMES
        )


class SceneName(object):
    # pylint: disable-msg=R0902
    def __init__(self):
        self.name = None
        self.group = None
        self.encoding_type = None
        self._source = None
        self.release_type = RELEASE_TYPE_UNKNOWN
        self.tags = []
        self.production_year = None
        self.cd_number = None
        self.season = None
        self.episode = None
        self.episode_name = None
        self.episode_date = None

    def _set_source(self, source):
        self._source = source

        if self._source in TV_SOURCE_NAMES:
            self.release_type = RELEASE_TYPE_TV
        elif self._source in MOVIE_SOURCE_NAMES:
            self.release_type = RELEASE_TYPE_MOVIE
        elif self._source in EBOOK_SOURCE_NAMES:
            self.release_type = RELEASE_TYPE_EBOOK
        else:
            self.release_type = RELEASE_TYPE_UNKNOWN

    def _get_source(self):
        return self._source

    source = property(fget=_get_source, fset=_set_source)

    @classmethod
    def parse(cls, release_name):
        # extract release group
        last_dash = release_name.rfind('-')
        parsed_name = cls()

        # look for the last dash in the name
        if last_dash != -1:
            # get the part after that dash
            parsed_name.group = release_name[last_dash + 1:]

            # if that has a . in it, disregard it
            if '.' in parsed_name.group:
                parsed_name.group = None
            else:
                # else remove that from the relase name
                release_name = release_name[:last_dash]

        # split the name by .
        release_parts = release_name.split('.')

        while release_parts:
            name_part = release_parts.pop()

            # check  for an encoding type
            encoding = check_tag_encoding_type(name_part)
            if encoding:
                parsed_name.encoding_type = encoding
                continue

            # check  for a source type
            source = check_tag_source_type(name_part)
            if source:
                parsed_name.source = source
                continue

            # check for one of the other tags
            tag = check_tag_valid_tag(name_part)
            if tag:
                parsed_name.tags.append(tag)
                continue

            # check for a cd number
            if CD_NUMBER_RE.match(name_part):
                parsed_name.cd_number = name_part
                continue

            # check for an episode number
            episode_match = SEASON_EPISODE_RE.match(name_part)
            if episode_match:
                parsed_name.season = episode_match.group(1)
                parsed_name.episode = episode_match.group(2)
                continue

            # check for a production year
            if YEAR_RE.match(name_part):
                parsed_name.production_year = name_part
                continue

            # if none of the above matches,
            # this must be part of the name itself
            # so stop checking the parts
            release_parts.append(name_part)
            break

        # Now for special cases

        # re-combine the name in the correct order
        parsed_name.name = '.'.join(release_parts)

        # Look to see if a season/episode tag is still present in the name
        # If so use the season/episode,
        # and anything after that is an episode name
        has_episode_name_match = SEASON_EPISODE_REMAINDER_RE.match(
                parsed_name.name)

        if has_episode_name_match:
            parsed_name.name = has_episode_name_match.group(1)
            parsed_name.season = has_episode_name_match.group(2)
            parsed_name.episode = has_episode_name_match.group(3)
            parsed_name.episode_name = has_episode_name_match.group(4)

        # Look to see if a date is embedded in the name
        # since this also screws up the above logic
        has_episode_date_match = EPISODE_DATE_REMAINDER_RE.match(
                parsed_name.name)

        if has_episode_date_match:
            parsed_name.name = has_episode_date_match.group(1)

            parsed_name.episode_date = date(
                int(has_episode_date_match.group(2)),
                int(has_episode_date_match.group(3)),
                int(has_episode_date_match.group(4)))

            parsed_name.episode_name = has_episode_date_match.group(5)

        return parsed_name
