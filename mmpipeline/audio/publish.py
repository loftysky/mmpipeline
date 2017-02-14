#!/usr/bin/env python

import argparse
import re
import os
import hashlib

from sgfs import SGFS
from sgpublish import Publisher


def main():
        
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--description')
    parser.add_argument('-p', '--project',
        help='Shotgun project to publish to. Good for debugging.')
    parser.add_argument('-n', '--dry-run', action='store_true',
        help='Dont do anything.')

    parser.add_argument('audio_files', nargs='+')
    args = parser.parse_args()


    sgfs = SGFS()
    sg = sgfs.session


    if args.project:
        project_input = args.project
        project = sgfs.parse_user_input(args.project, ['Project'])
    else:
        project_input = args.audio_files[0]
        project = sgfs.entities_from_path(args.audio_files[0], 'Project')
    if not project:
        print >> sys.stderr, 'Could not find Shotgun project for', project_input
        exit(1)


    for path in args.audio_files:

        print path

        name, ext = os.path.splitext(os.path.basename(path))
        m = re.search(r'sq(\d{2})_s[hc](\d{2})', name, re.I)

        if not m:
            print '\tCould not parse filename:', name
            continue

        shot_code = 'Sq%s_Sh%s' % m.groups()
        shot = sg.find_one('Shot', [
            ('project', 'is', project),
            ('code', 'is', shot_code),
        ])
        if not shot:
            print '\tCould not find shot.'
            continue
        print '   ', shot

        task = sg.find_one('Task', [
            ('entity', 'is', shot),
            ('step.Step.short_name', 'is', 'audio'),
        ])
        if not task:
            print '\tCould not find "audio" task.'
            continue
        print '   ', task

        pubs = sg.find('PublishEvent', [
            ('sg_link', 'is', task),
            ('sg_type', 'is', 'audio_proxy'),
        ], ['sg_path', 'sg_version'])
        if pubs:
            pubs.sort(key=lambda p: p['sg_version'])
            pub = pubs[-1]
            print '   ', pub
            existing_md5 = hashlib.md5(open(pub['sg_path'], 'rb').read()).hexdigest()
            new_md5 = hashlib.md5(open(path, 'rb').read()).hexdigest()
            if existing_md5 == new_md5:
                print '   MD5 matches previous publish!'
                continue


        if args.dry_run:
            continue

        with Publisher(link=task, name='dialogue', type='audio_proxy') as publisher:
            publisher.description = args.description
            publisher.path = publisher.add_file(path)

        print '   ', publisher.entity
