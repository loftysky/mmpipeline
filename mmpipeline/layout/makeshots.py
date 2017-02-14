#!/usr/bin/env python

import argparse
import os
import sys

from sgfs import SGFS


def main():
        
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--dry-run', action='store_true',
        help='Dont do anything.')
    parser.add_argument('-v', '--verbose', action='store_true',
        help='Dont do anything verbosely.')

    parser.add_argument('-c', '--create-structure', action='store_true')
    parser.add_argument('-s', '--sequence', required=True)
    parser.add_argument('-N', '--shots', type=int, required=True)
    args = parser.parse_args()

    sgfs = SGFS()
    sg = sgfs.session


    sequence = sgfs.parse_user_input(args.sequence, ['Sequence'])
    if not sequence:
        print >> sys.stderr, 'Could not find sequence:', args.sequence
        exit(1)

    if args.shots < 1:
        print >> sys.stderr, 'Shots must be positive number, got:', args.shots
        exit(2)


    project = sequence.fetch('project')

    task_template = sg.find_one('TaskTemplate', [
        ('entity_type', 'is', 'Shot'),
        ('sg_projects', 'is', project),
    ])


    existing_shots = sg.find('Shot', [
        ('sg_sequence', 'is', sequence),
    ], ['code'])
    existing_shots_by_name = {}
    for shot in existing_shots:
        existing_shots_by_name[shot['code']] = shot


    for shot_num in xrange(1, args.shots + 1):

        shot_name = sequence['code'] + '_Sh%02d' % shot_num
        shot = existing_shots_by_name.get(shot_name)

        if shot:
            print 'Shot', shot_name, 'already exists.'

        else:
            # This shot doesn't exist yet!

            print 'Making', shot_name

            if not args.dry_run:
                shot = sg.create('Shot', {
                    'code': shot_name,
                    'task_template': task_template,
                    'sg_sequence': sequence,
                    'project': project,
                })
                if args.verbose:
                    print '   ', shot

        if args.create_structure and not args.dry_run:
            sgfs.create_structure(shot, verbose=args.verbose)

