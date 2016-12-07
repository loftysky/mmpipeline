#!/usr/bin/env python
import argparse
import os

from sgsession import Session


parser = argparse.ArgumentParser()
parser.add_argument('-d', '--description')
parser.add_argument('-n', '--dry-run', action='store_true',
    help='Dont do anything.')
parser.add_argument('-v', '--verbose', action='store_true',
    help='Dont do anything verbosely.')


parser.add_argument('--project')
parser.add_argument('--seq')
parser.add_argument('--shot', type=int)
args = parser.parse_args()

sg = Session()
all_projects_filters = [['status', 'is', 'active']]
all_projects = sg.find('Project',all_projects_filters)

def checkShots(seqname, shots, shotnum):
    temp_shots = []
    shot_code = []
    shotnum = shotnum + 1
    for x in xrange(1, shotnum):
        temp_shots.append(seqname + '_Sh%02d' % x)
    for shot in shots:
        shot_code.append(shot['code'])
    for val in temp_shots:
        if val in shot_code:
            print "This is already in the sequence", val
        else: 
            shot = sg.create('Shot', {
            'code': val,
            'task_template': task_template,
            'sg_sequence': seq,
            'project': project,
            })
            print "Making", shot
try: 

    #check project for sequence: 
    filters = [['name', 'is', args.project]]
    check_project = sg.find_one('Project', filters)
    #check if Project is in Shotgun: 
    if check_project not in all_projects:
        print args.project + " not found. Do you mean one of these projects? Don't forget to add '' around titles with multiple words!"
        for aproject in all_projects:
            print aproject
    else: 
            print 'CHECKING PROJECT', check_project['name'], check_project['id']
        # check if seq is in Project
            seq_filters = [('project', 'is', {'type': 'Project', 'name':check_project['name'], 'id':check_project['id'] })]
            check_seq = sg.find('Sequence', seq_filters)
            for seq in check_seq:
                if args.seq != seq['code']:
                    statement = "Can't find " + args.seq + " sequence in " + args.project 
                else:
                    shot_filters = [('sg_sequence', 'is', {'type': 'Sequence', 'id': seq['id']})]
                    check_shot = sg.find('Shot', shot_filters, 'code')
                    project = seq.fetch('project')
                    task_filters = [('entity_type', 'is', 'Shot'), ('sg_projects', 'is', project)]
                    task_template = sg.find_one('TaskTemplate', task_filters)
                    if args.dry_run:
                        statement = ""
                        continue

                    checkShots(args.seq, check_shot, args.shot)
                    statement = ""     
            if statement != "":
                print statement
except:
        print "Something went wrong."

