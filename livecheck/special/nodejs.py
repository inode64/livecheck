"""NodeJS functions."""
from __future__ import annotations

from typing import TYPE_CHECKING
import logging
import subprocess as sp

from livecheck.utils import check_program

from .utils import build_compress, remove_url_ebuild, search_ebuild

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = ('check_nodejs_requirements', 'remove_nodejs_url', 'update_nodejs_ebuild')

logger = logging.getLogger(__name__)


def remove_nodejs_url(ebuild_content: str) -> str:
    """Remove ``node_modules.tar.xz`` line from ebuild."""
    return remove_url_ebuild(ebuild_content, '-node_modules.tar.xz')


def get_nodejs_install_command(manager: str) -> tuple[str, ...]:
    """Return the command tuple to install dependencies."""
    commands = {
        'npm': ('npm', 'install', '--audit=false', '--color=false', '--progress=false', '--ignore-scripts'),
        'yarn': ('yarn', 'install', '--ignore-scripts', '--non-interactive', '--silent'),
        'pnpm': ('pnpm', 'install', '--ignore-scripts', '--silent'),
    }
    return commands.get(manager.lower(), commands['npm'])


def update_nodejs_ebuild(ebuild: str, path: str | None,
                         fetchlist: Mapping[str, tuple[str, ...]],
                         manager: str = 'npm') -> None:
    """Update a NodeJS-based ebuild."""
    package_path, temp_dir = search_ebuild(ebuild, 'package.json', path)
    if not package_path:
        return

    try:
        command = get_nodejs_install_command(manager)
        sp.run(command, cwd=package_path, check=True)
    except sp.CalledProcessError:
        logger.exception("Error running '%s install'.", manager)
        return

    build_compress(temp_dir, package_path, 'node_modules', '-node_modules.tar.xz', fetchlist)


def check_nodejs_requirements(manager: str = 'npm') -> bool:
    """Check if the required package manager is installed."""
    binary = get_nodejs_install_command(manager)[0]
    if not check_program(binary, ['--version']):
        logger.error('%s is not installed', binary)
        return False
    return True
