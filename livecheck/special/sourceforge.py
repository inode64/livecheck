import os
import re
import xml.etree.ElementTree as etree
from urllib.parse import urlparse

from ..settings import LivecheckSettings
from ..utils.portage import get_last_version, catpkg_catpkgsplit
from ..utils import get_content
from .utils import get_archive_extension

__all__ = ["get_latest_sourceforge_package"]

SOURCEFORGE_DOWNLOAD_URL = 'https://sourceforge.net/projects/%s/rss'


def extract_repository(url: str, pkg: str) -> str:
    parsed = urlparse(url)
    if '/projects/' in parsed.path or '/project/' in parsed.path:
        return parsed.path.split('/')[2]

    n = parsed.netloc
    if 'downloads.sourceforge.net' in n or 'download.sourceforge.net' in n or 'sf.net' in n:
        return parsed.path.split('/')[1]

    if (m := re.match(r'^([^\.]+)\.(sf|sourceforge)\.(net|io|jp)$', n)):
        return m.group(1)

    return pkg


def get_latest_sourceforge_package(src_uri: str, ebuild: str, settings: LivecheckSettings) -> str:

    _, pkg, _, _ = catpkg_catpkgsplit(ebuild)

    repository = extract_repository(src_uri, pkg)
    url = SOURCEFORGE_DOWNLOAD_URL % (repository)

    if not (response := get_content(url)):
        return ''

    results = []

    for item in etree.fromstring(response.text).findall(".//item"):
        title = item.find("title")
        version = os.path.basename(title.text) if title is not None and title.text else ''
        if version and get_archive_extension(version):
            results.append({"tag": version})

    if last_version := get_last_version(results, repository, ebuild, settings):
        return last_version['version']

    return ''
