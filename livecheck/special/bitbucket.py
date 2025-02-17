from urllib.parse import urlparse

from ..settings import LivecheckSettings
from ..utils import get_content, is_sha
from ..utils.portage import get_last_version
from .utils import get_archive_extension, log_unhandled_commit

__all__ = ("get_latest_bitbucket_package", "is_bitbucket", "BITBUCKET_METADATA",
           "get_latest_bitbucket", "get_latest_bitbucket_metadata")

# doc: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-refs/#api-repositories-workspace-repo-slug-refs-tags-get
BITBUCKET_TAG_URL = 'https://api.bitbucket.org/2.0/repositories/%s/%s/refs/tags'
# doc: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-downloads/#api-repositories-workspace-repo-slug-downloads-get
BITBUCKET_DOWNLOAD_URL = 'https://api.bitbucket.org/2.0/repositories/%s/%s/downloads'
BITBUCKET_METADATA = 'bitbucket'
MAX_ITERATIONS = 4


def get_latest_bitbucket_package(path: str, ebuild: str,
                                 settings: LivecheckSettings) -> tuple[str, str]:
    workspace, repository = path.strip("/").split('/')[:2]

    url = BITBUCKET_TAG_URL % (workspace, repository)

    if not (tags_response := get_content(url)):
        return '', ''

    results: list[dict[str, str]] = [{
        "tag": tag.get("name", ""),
        "id": tag.get("target", {}).get("hash", "")
    } for tag in tags_response.json().get("values", [])]

    # The tag may not be created and you need to know the downloads
    # for the latest versions
    url = BITBUCKET_DOWNLOAD_URL % (workspace, repository)
    iteration_count = 0

    while url and iteration_count < MAX_ITERATIONS:
        if not (r := get_content(url)):
            break
        data = r.json()

        results.extend({
            "tag": item.get('name', ''),
            "id": ''
        } for item in data.get("values", []) if get_archive_extension(item.get('name',)))

        url = data.get('next')
        iteration_count += 1

    if last_version := get_last_version(results, repository, ebuild, settings):
        return last_version['version'], last_version["id"]

    return '', ''


def get_latest_bitbucket(url: str, ebuild: str,
                         settings: LivecheckSettings) -> tuple[str, str, str]:
    last_version = top_hash = hash_date = ''

    if is_sha(urlparse(url).path):
        log_unhandled_commit(ebuild, url)
    else:
        last_version, top_hash = get_latest_bitbucket_package(url, ebuild, settings)

    return last_version, top_hash, hash_date


def is_bitbucket(url: str) -> bool:
    return urlparse(url).netloc in 'bitbucket.org'


def get_latest_bitbucket_metadata(remote: str, ebuild: str,
                                  settings: LivecheckSettings) -> tuple[str, str]:
    return get_latest_bitbucket_package(f'https://bitbucket.org/{remote}', ebuild, settings)
