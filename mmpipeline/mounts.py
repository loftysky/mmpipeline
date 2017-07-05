import argparse
import collections
import logging
import os
import re
import subprocess
import sys


log = logging.getLogger(__name__)


REMOTE_FS_TYPES = set('nfs smb samba afp'.split())
LOCAL_FS_TYPES = set('hfs ext3 ext4'.split())


_MountBase = collections.namedtuple('Mount', ['device', 'path', 'type', 'flags'])
class Mount(_MountBase):

    @property
    def is_local(self):
        return self.type in LOCAL_FS_TYPES

    @property
    def is_remote(self):
        return self.type in REMOTE_FS_TYPES


def _parse_mounts(raw=None):
    """Get list of mounted filesystems.
    Each mount is a namedtuple with fields: device, path, type, and flags.
    """
    raw = raw or subprocess.check_output(['mount'])
    if sys.platform == 'darwin':
        return _parse_darwin_mounts(raw)
    elif sys.platform.startswith('linux'):
        return _parse_linux_mounts(raw)
    else:
        raise RuntimeError('cannot parse mounts for %s' % sys.platform)


def _parse_darwin_mounts(raw):
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^(.+?) on (/.*?) \(([^,]+)(?:, )?(.*?)\)$', line)
        if not m:
            log.warning('could not parse mount line %r' % line)
            continue
        device, path, type_, flags = m.groups()
        yield Mount(device, path, type_, frozenset(flags.split(', ')))


def _parse_linux_mounts(raw):
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^(.+?) on (/.*?) type (.+?) \((.+?)\)$', line)
        if not m:
            log.warning('could not parse mount line %r' % line)
            continue
        device, path, type_, flags = m.groups()
        yield Mount(device, path, type_, frozenset(flags.split(',')))


class MountSet(tuple):

    def __new__(cls, mounts=None):
        return super(MountSet, cls).__new__(cls, mounts or _parse_mounts())

    def get_mount_at_path(self, path):
        path = os.path.realpath(path) # Otherwise symlinks can mess us up.
        for mount in self:
            if mount.path == path:
                return mount

    def get_mount_containing_path(self, path):
        """Get the mount corresponding to the given path."""
        path = os.path.realpath(path) # Otherwise symlinks can mess us up.
        for mount in sorted(self, key=lambda m: len(m.path), reverse=True):
            if path.startswith(mount.path) and (mount.path.endswith('/') or path[len(mount.path):len(mount.path)+1] in ('/', '')):
                return mount


if __name__ == '__main__':
    for mount in MountSet():
        print '{:1}{:1} {}'.format(
            'L' if mount.is_local else '-',
            'R' if mount.is_remote else '-',
            mount,
        )

