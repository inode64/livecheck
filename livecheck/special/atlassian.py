"""
Grabbers for Atlassian products (Bitbucket Runner, FishEye, Crucible, Crowd).
Functional style, no classes.
"""

import re
import requests
from xml.etree import ElementTree
from livecheck.utils.portage import get_last_version


BITBUCKET_RUNNER_CHANGELOG = "https://product-downloads.atlassian.com/software/bitbucket/pipelines/CHANGELOG.md"
FISHEYE_RSS = "https://my.atlassian.com/download/feeds/fisheye.rss"
CRUCIBLE_RSS = "https://my.atlassian.com/download/feeds/crucible.rss"
CROWD_RSS = "https://my.atlassian.com/download/feeds/crowd.rss"

ATLASSIAN_DOMAINS = [
    "atlassian.com",
    "my.atlassian.com",
    "product-downloads.atlassian.com",
]

def is_atlassian(url: str) -> bool:
    """Return True if the url is for an Atlassian product (Bitbucket Runner, FishEye, Crucible, Crowd)."""
    return any(domain in url for domain in ATLASSIAN_DOMAINS)


def get_latest_bitbucket_runner(ebuild=None, settings=None):
    """Get latest version from Bitbucket Pipelines Runner changelog markdown. If ebuild/settings are provided, use get_last_version logic."""
    resp = requests.get(BITBUCKET_RUNNER_CHANGELOG, timeout=10)
    resp.raise_for_status()
    data = resp.text
    versions = re.findall(r"^## ([0-9.]+) ", data, re.MULTILINE)
    if not versions:
        raise ValueError("Could not find version in Bitbucket Runner changelog.")
    if ebuild and settings:
        results = [{"tag": v} for v in versions]
        last = get_last_version(results, "bitbucket-runner", ebuild, settings)
        return last["version"] if last else ""
    return versions[0]


def get_latest_atlassian_rss(url, ebuild=None, settings=None, repo_name=None):
    """Get latest version from Atlassian product RSS feed (FishEye, Crucible, Crowd). If ebuild/settings are provided, use get_last_version logic."""
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.text
    root = ElementTree.fromstring(data)
    versions = []
    for item in root.findall('.//item'):
        title = item.find('title')
        if title is not None:
            m = re.search(r"([0-9]+\.[0-9]+(\.[0-9]+)?)", title.text)
            if m:
                versions.append(m.group(1))
    if not versions:
        raise ValueError(f"Could not find version in RSS feed: {url}")
    if ebuild and settings:
        repo = repo_name or url.split('/')[-1].split('.')[0]
        results = [{"tag": v} for v in versions]
        last = get_last_version(results, repo, ebuild, settings)
        return last["version"] if last else ""
    return versions[0]


def get_latest_fisheye(ebuild=None, settings=None):
    return get_latest_atlassian_rss(FISHEYE_RSS, ebuild, settings, repo_name="fisheye")

def get_latest_crucible(ebuild=None, settings=None):
    return get_latest_atlassian_rss(CRUCIBLE_RSS, ebuild, settings, repo_name="crucible")

def get_latest_crowd(ebuild=None, settings=None):
    return get_latest_atlassian_rss(CROWD_RSS, ebuild, settings, repo_name="crowd")
