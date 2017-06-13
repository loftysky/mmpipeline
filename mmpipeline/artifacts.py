import os

from .utils import makedirs


source_root = '/Volumes/CGroot'
artifacts_root = '/Volumes/CGartifacts'


def to_shadow_dimension(path, make_parent=False):
    """Convert a CGroot path to a CGartifacts path."""

    path = os.path.abspath(path)
    rel_path = os.path.relpath(path, source_root)
    if rel_path.startswith('../'): 
        raise ValueError('Source is not in CGroot.', path)

    new_path = os.path.join(artifacts_root, rel_path)
    if make_parent: 
        makedirs(os.path.dirname(new_path))

    return new_path
