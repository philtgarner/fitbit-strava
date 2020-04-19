import urllib.parse as urlparse
from urllib.parse import parse_qs


def get_parameter(query, param):
    url = f'http://example.org{query}'
    parsed = urlparse.urlparse(url)
    try:
        return parse_qs(parsed.query)[param]
    except KeyError:
        return None
