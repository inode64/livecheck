import tempfile
from pathlib import Path

from loguru import logger
from .utils import search_ebuild

from ..settings import LivecheckSettings
from ..utils.portage import get_last_version, catpkg_catpkgsplit
from ..utils import get_content

__all__ = ("get_latest_jetbrains_package", "update_jetbrains_ebuild")

JETBRAINS_TAG_URL = 'https://data.services.jetbrains.com/products'


def get_latest_jetbrains_package(ebuild: str, development: bool, restrict_version: str,
                                 settings: LivecheckSettings) -> str:
    product_name = {
        'phpstorm': 'PhpStorm',
        'pycharm-community': 'PyCharm Community Edition',
        'pycharm-professional': 'PyCharm Professional Edition',
        'idea-community': 'IntelliJ IDEA Community Edition',
        'clion': 'CLion',
        'goland': 'GoLand',
    }

    _, _, product_code, _ = catpkg_catpkgsplit(ebuild)

    if not (response := get_content(JETBRAINS_TAG_URL)):
        return ''

    product_code = product_name.get(product_code, product_code)

    results: list[dict[str, str]] = []
    for product in response.json():
        if product['name'] == product_code:
            for release in product['releases']:
                if (release['type'] == 'eap' or release['type'] == 'rc') and not development:
                    continue
                if 'linux' in release.get('downloads', ''):
                    results.append({"tag": release['version']})

    if last_version := get_last_version(results, '', ebuild, development, restrict_version,
                                        settings):
        return last_version['tag']

    return ''


def update_jetbrains_ebuild(ebuild: str | Path) -> None:
    package_path, _ = search_ebuild(str(ebuild), 'product-info.json')
    if not (version := package_path.split('/')[-1]):
        logger.warning('No version found in the tar.gz file.')
        return

    version = version.split('-', 1)[-1]

    ebuild = Path(ebuild)
    tf = tempfile.NamedTemporaryFile(mode='w',
                                     prefix=ebuild.stem,
                                     suffix=ebuild.suffix,
                                     delete=False,
                                     dir=ebuild.parent)
    with ebuild.open('r', encoding='utf-8') as f:
        for line in f.readlines():
            if line.startswith('MY_PV='):
                logger.debug('Found MY_PV= line.')
                tf.write(f'MY_PV="{version}"\n')
            else:
                tf.write(line)
    ebuild.unlink()
    Path(tf.name).rename(ebuild).chmod(0o0644)
