from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from functools import cache
from http import HTTPStatus
from urllib.parse import urlparse
import hashlib
import logging

import requests

from .credentials import get_api_credentials

log = logging.getLogger(__name__)


@dataclass
class TextDataResponse:
    """Used for data URI responses."""
    text: str
    status_code: int = HTTPStatus.OK  # Default status code for successful response

    def raise_for_status(self) -> None:
        pass


@cache
def session_init(module: str) -> requests.Session:
    session = requests.Session()
    if module == 'github':
        token = get_api_credentials('github.com')
        if token:
            session.headers['Authorization'] = f'Bearer {token}'
        session.headers['Accept'] = 'application/vnd.github.v3+json'
    elif module == 'xml':
        session.headers['Accept'] = 'application/xml'
    elif module == 'json':
        session.headers['Accept'] = 'application/json'
    elif module == 'gitlab':
        token = get_api_credentials('gitlab.com')
        if token:
            session.headers['Authorization'] = f'Bearer {token}'
        session.headers['Accept'] = 'application/json'
    elif module == 'bitbucket':
        token = get_api_credentials('bitbucket.org')
        if token:
            session.headers['Authorization'] = f'Bearer {token}'
        session.headers['Accept'] = 'application/json'
    session.headers['timeout'] = '30'
    return session


def get_content(url: str) -> requests.Response:
    parsed_uri = urlparse(url)
    log.debug('Fetching %s', url)

    if parsed_uri.hostname == 'api.github.com':
        session = session_init('github')
    elif parsed_uri.hostname == 'api.gitlab.com':
        session = session_init('gitlab')
    elif parsed_uri.hostname == 'api.bitbucket.org':
        session = session_init('bitbucket')
    elif parsed_uri.hostname == 'repology.org':
        session = session_init('json')
        session.headers['User-Agent'] = 'DistroWatch'
    elif url.endswith(('.atom', '.xml')):
        session = session_init('xml')
    elif url.endswith('json'):
        session = session_init('json')
    else:
        session = session_init('')

    r: TextDataResponse | requests.Response
    try:
        r = session.get(url)
    except requests.RequestException:
        log.exception('Caught error {e} attempting to fetch {url}')
        r = requests.Response()
        r.status_code = HTTPStatus.SERVICE_UNAVAILABLE
        return r
    if r.status_code not in {
            HTTPStatus.OK, HTTPStatus.CREATED, HTTPStatus.ACCEPTED, HTTPStatus.PARTIAL_CONTENT,
            HTTPStatus.MOVED_PERMANENTLY, HTTPStatus.FOUND, HTTPStatus.TEMPORARY_REDIRECT,
            HTTPStatus.PERMANENT_REDIRECT
    }:
        log.error('Error fetching %s. Status code: %d', url, r.status_code)
    elif not r.text:
        log.warning('Empty response for %s.', url)

    return r


@cache
def hash_url(url: str) -> tuple[str, str, int]:
    h_blake2b = hashlib.blake2b()
    h_sha512 = hashlib.sha512()
    size = 0
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    h_blake2b.update(chunk)
                    h_sha512.update(chunk)
                    size += len(chunk)
        return h_blake2b.hexdigest(), h_sha512.hexdigest(), size
    except requests.RequestException:
        log.exception('Error hashing URL %s.', url)

    return '', '', 0


@cache
def get_last_modified(url: str) -> str:
    try:
        with requests.head(url, timeout=30) as r:
            r.raise_for_status()
            if last_modified := r.headers['last-modified']:
                return parsedate_to_datetime(last_modified).strftime('%Y%m%d')

    except requests.RequestException:
        log.exception('Error fetching last modified header for %s.', url)

    return ''
