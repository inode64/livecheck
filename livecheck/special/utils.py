from pathlib import Path
import logging
import os
import tarfile
import tempfile

from xdg.BaseDirectory import save_cache_path

from ..utils.portage import get_distdir, unpack_ebuild

__all__ = ("get_project_path", "remove_url_ebuild", "search_ebuild", "build_compress",
           "get_archive_extension", "EbuildTempFile")

logger = logging.getLogger(__name__)


def get_project_path(package_name: str) -> Path:
    return Path(save_cache_path(f"livecheck/{package_name}"))


def remove_url_ebuild(ebuild: str, remove: str) -> str:
    lines = ebuild.split('\n')
    filtered_lines = []
    for _, line in enumerate(lines):
        original_line = line
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith('#'):
            filtered_lines.append(original_line)
            continue
        if remove in stripped_line:
            url = stripped_line.strip(' "\'')
            if url.endswith(remove):
                if stripped_line.endswith(('"', "'")) and (stripped_line.count('"') == 1
                                                           or stripped_line.count("'") == 1):
                    filtered_lines.append(stripped_line[-1])
                continue
        filtered_lines.append(original_line)
    return '\n'.join(filtered_lines)


def search_ebuild(ebuild: str, archive: str, path: str | None = None) -> tuple[str, str]:
    temp_dir = unpack_ebuild(ebuild)
    if temp_dir == "":
        logger.warning("Error unpacking the ebuild.")
        return "", ""

    if path:
        # Search first directory in temp_dir
        for root, _, _ in os.walk(temp_dir):
            # check if relative path is in the root
            if path in root:
                return root, temp_dir
    else:
        for root, _, files in os.walk(temp_dir):
            if archive in files:
                return root, temp_dir

    logger.error("Error searching the \"{archive}\" inside package.")

    return "", ""


def build_compress(temp_dir: str, base_dir: str, directory: str, extension: str,
                   fetchlist: dict[str, str]) -> bool:

    vendor_dir = os.path.join(base_dir, directory)
    if not os.path.exists(vendor_dir):
        logger.warning("The directory vendor was not created.")
        return False

    if not (filename := next(iter(fetchlist.keys()), None)):
        return False

    if not (archive_ext := get_archive_extension(filename)):
        logger.warning("Invalid extension.")
        return False

    if extension in filename:
        vendor_archive_name = filename
    else:
        base_name = filename[:-len(archive_ext)]
        vendor_archive_name = f"{base_name}{extension}"
    vendor_archive_path = os.path.join(get_distdir(), vendor_archive_name)

    vendor_path = Path(base_dir).resolve()
    base_path = Path(temp_dir).resolve()

    relative_path = os.path.join(vendor_path.relative_to(base_path), directory)

    with tarfile.open(vendor_archive_path, "w:xz") as tar:
        tar.add(vendor_dir, arcname=str(relative_path))

    return True


def get_archive_extension(filename: str) -> str:
    filename = filename.lower()
    for ext in [
            'tar.gz', 'tar.xz', 'tar.bz2', 'tar.lz', 'tar.zst', 'tc.gz', 'tar.z', 'gz', 'xz', 'zip',
            'tbz2', 'bz2', 'tbz', 'txz', 'tar', 'tgz', 'rar', '7z'
    ]:
        if filename.endswith('.' + ext):
            return '.' + ext

    return ''


class EbuildTempFile:
    def __init__(self, ebuild: str):
        self.ebuild = Path(ebuild)
        self.temp_file: Path | None = None

    def __enter__(self) -> Path:
        self.temp_file = Path(
            tempfile.NamedTemporaryFile(mode='w',
                                        prefix=self.ebuild.stem,
                                        suffix=self.ebuild.suffix,
                                        delete=False,
                                        dir=self.ebuild.parent).name)
        return self.temp_file

    def __exit__(self, exc_type: object, exc_value: BaseException | None,
                 traceback: object) -> bool:
        if exc_type is None:
            if not self.temp_file or not self.temp_file.exists() or self.temp_file.stat(
            ).st_size == 0:
                logger.error("The temporary file is empty or missing.")
                return False

            self.ebuild.unlink(missing_ok=True)

            if self.ebuild.exists():
                logger.error("Error removing the original ebuild file.")
                return False

            self.temp_file.rename(self.ebuild)
            self.ebuild.chmod(0o0644)

            if not self.ebuild.exists():
                logger.error("Error renaming the temporary file.")
                return False

        if self.temp_file and self.temp_file.exists():
            self.temp_file.unlink(missing_ok=True)

        return True


def log_unhandled_commit(catpkg: str, src_uri: str) -> None:
    logger.warning('Unhandled commit: %s SRC_URI: %s', catpkg, src_uri)
