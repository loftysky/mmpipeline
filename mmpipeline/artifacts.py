import os
import sys

from .utils import makedirs
from .mounts import MountSet

source_root = '/Volumes/CGroot'
artifacts_root = '/Volumes/CGartifacts'

_mounts = None

def _goes_up(rel_path):
    return rel_path.startswith('../')

def _convert(src_path, src_root, dst_root, make_parent, allow_passthrough, assert_mount=True):

    global _mounts

    # The destination must always exist.
    if not os.path.exists(dst_root):
        raise ValueError("Destination root does not exist.", dst_root)

    # The destination must usually be a mount.
    if assert_mount:
        _mounts = _mounts or MountSet()
        mount = _mounts.get_mount_at_path(dst_root)
        if mount is None:
            raise ValueError("Destination root is not a mount.", dst_root)

    src_path = os.path.abspath(src_path)
    rel_path = os.path.relpath(src_path, src_root)
    if _goes_up(rel_path):
        if allow_passthrough and src_path.startswith(dst_root + '/'):
            return src_path
        raise ValueError('Source is not in %s.' % (src_root, ), src_path)

    dst_path = os.path.join(dst_root, rel_path)
    if make_parent: 
        makedirs(os.path.dirname(dst_path))

    return dst_path


def is_shadow_dimension(src_path):
    src_path = os.path.abspath(src_path)
    rel_path = os.path.relpath(src_path, artifacts_root)
    return not _goes_up(rel_path)

def to_shadow_dimension(path, make_parent=False, allow_passthrough=True):
    """Convert a CGroot path to a CGartifacts path."""
    return _convert(path, source_root, artifacts_root, make_parent, allow_passthrough)

def from_shadow_dimension(shadow_path, make_parent=False, allow_passthrough=True):
    """Convert a CGartifacts path to a CGroot path."""
    return _convert(shadow_path, artifacts_root, source_root, make_parent, allow_passthrough)


if __name__ == '__main__':
    for x in sys.argv[1:]:
        print to_shadow_dimension(x, make_parent=False)
