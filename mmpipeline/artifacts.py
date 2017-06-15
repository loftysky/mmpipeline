import os

from .utils import makedirs


source_root = '/Volumes/CGroot'
artifacts_root = '/Volumes/CGartifacts'


def _goes_up(rel_path):
    return rel_path.startswith('../')

def _convert(src_path, src_root, dst_root, make_parent, allow_passthrough):

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

