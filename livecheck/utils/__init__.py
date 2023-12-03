"""Utility functions."""
from dataclasses import dataclass
from functools import lru_cache
from itertools import groupby
import logging
from pathlib import Path
from typing import TypeVar, cast
from collections.abc import Callable, Iterable, Iterator, Sequence
import operator
import re
import xml.etree.ElementTree as etree

import yaml

__all__ = ('TextDataResponse', 'assert_not_none', 'chunks', 'dash_to_underscore', 'dotize',
           'get_github_api_credentials', 'is_sha', 'latest_jetbrains_versions',
           'make_github_grit_commit_re', 'make_github_grit_title_re', 'prefix_v')

logger = logging.getLogger(__name__)
T = TypeVar('T')
# From parse-package-name
# https://github.com/egoist/parse-package-name/blob/main/src/index.ts
RE_SCOPED = r'^(@[^\/]+\/[^@\/]+)(?:@([^\/]+))?(\/.*)?$'
RE_NON_SCOPED = r'^([^@\/]+)(?:@([^\/]+))?(\/.*)?$'


def make_github_grit_commit_re(version: str) -> str:
    return (r'<id>tag:github.com,2008:Grit::Commit/([0-9a-f]{' + str(len(version)) +
            r'})[0-9a-f]*</id>')


def make_github_grit_title_re() -> str:
    return r'<title>\s+.*v([0-9][^ <]+) '


def dotize(s: str) -> str:
    ret = s.replace('-', '.').replace('_', '.')
    logger.debug('dotize(): %s -> %s', s, ret)
    return ret


def is_sha(s: str) -> bool:
    return bool((len(s) == 7 or len(s) > 8) and re.match(r'^[0-9a-f]+$', s))


def chunks(seq: Sequence[T], n: int) -> Iterator[Sequence[T]]:
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


class InvalidPackageName(ValueError):
    def __init__(self, pkg: str):
        super().__init__(f'Invalid package name: {pkg}')


def parse_npm_package_name(s: str) -> tuple[str, str | None, str | None]:
    if not (m := re.match(RE_SCOPED, s) or re.match(RE_NON_SCOPED, s)):
        raise InvalidPackageName(s)
    return m[1], m[2], m[3]


@lru_cache
def get_github_api_credentials() -> str:
    with Path('~/.config/gh/hosts.yml').expanduser().open() as f:
        data = yaml.safe_load(f)
    return cast(str, data['github.com']['oauth_token'])


def prefix_v(s: str) -> str:
    return f'v{s}'


def latest_jetbrains_versions(xml_content: str, product_name: str) -> Iterator[dict[str, str]]:
    return (dict(version=z.attrib['version'], fullNumber=z.attrib['fullNumber']) for z in [
        y
        for y in [x for x in etree.fromstring(xml_content)
                  if x.attrib.get('name') == product_name][0] if y.attrib.get('status') == 'release'
    ][0])


def unique_justseen(iterable: Iterable[T], key: Callable[[T], T] | None = None) -> Iterator[T]:
    """List unique elements, preserving order. Remember only the element just seen."""
    return (next(x) for x in (operator.itemgetter(1)(y) for y in groupby(iterable, key)))


def assert_not_none(x: T | None) -> T:
    assert x is not None
    return x


def dash_to_underscore(s: str) -> str:
    return s.replace('-', '_')


@dataclass
class TextDataResponse:
    text: str

    def raise_for_status(self) -> None:
        pass
