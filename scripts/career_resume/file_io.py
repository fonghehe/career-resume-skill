"""Publish complete generated files and clean up failed exclusive writes."""

from contextlib import contextmanager
import os
from pathlib import Path
import shutil
import stat
import tempfile


def atomic_write(path, data):
    """Replace a generated artifact only after a complete sibling file is flushed."""
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Refusing a symlink output path.')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.career-write-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if path.is_file():
            shutil.copymode(path, temporary)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


@contextmanager
def new_file(path):
    """Open exclusively; failure cleanup only removes the inode this call created."""
    path = Path(path)
    owned = None
    try:
        with path.open('xb') as stream:
            owned = os.fstat(stream.fileno())
            yield stream
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        if owned is not None:
            try:
                current = path.lstat()
            except FileNotFoundError:
                pass
            else:
                same_file = (current.st_dev, current.st_ino) == (owned.st_dev, owned.st_ino)
                if same_file and stat.S_ISREG(current.st_mode):
                    path.unlink()
        raise


def write_new(path, data):
    """Write new bytes without replacing an existing file."""
    with new_file(path) as stream:
        stream.write(data)
