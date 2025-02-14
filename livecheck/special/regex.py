import re
import xml.etree.ElementTree as etree

from loguru import logger

from ..constants import RSS_NS, SEMVER_RE
from ..settings import LivecheckSettings
from ..utils import get_content, is_sha
from ..utils.portage import catpkg_catpkgsplit, get_last_version

__all__ = ('get_latest_regex_package',)


def adjust_regex(version: str, regex: str, settings: LivecheckSettings, cp: str,
                 text: str) -> list[str]:
    logger.debug(f'Using RE: "{regex}"')

    # Ignore beta/alpha/etc if semantic and coming from GitHub
    if (re.match(SEMVER_RE, version) and regex.startswith('archive/')
            and settings.semver.get(cp, True)):
        logger.debug('Adjusting RE for semantic versioning')
        regex = regex.replace(r'([^"+)', r'v?(\d+\.\d+(?:\.\d+)?)')
        logger.debug(f'Adjusted RE: {regex}')

    return re.findall(regex, text)


def get_latest_regex_package(ebuild: str, url: str, regex: str, version: str,
                             settings: LivecheckSettings) -> tuple[str, str, str]:

    cp, _, _, ebuild_version = catpkg_catpkgsplit(ebuild)

    r = get_content(url)
    if not r:
        return '', '', ''

    results: list[dict[str, str]] = []
    for result in adjust_regex(version, regex, settings, cp, r.text):
        if is_sha(result) and not results:
            hash_date = ''
            try:
                updated_el = etree.fromstring(r.text).find('entry/updated', RSS_NS)
                assert updated_el is not None
                assert updated_el.text is not None
                if re.search(r'(2[0-9]{7})', ebuild_version):
                    hash_date = updated_el.text.split('T')[0].replace('-', '')
                    logger.debug(f'Use updated date {hash_date} for commit {result}')
            except etree.ParseError:
                logger.error(f'Error parsing {url}')
            return result, hash_date, url
        results.append({"tag": result})

    if last_version := get_last_version(results, '', ebuild, settings):
        return last_version['version'], '', ''

    return '', '', ''
