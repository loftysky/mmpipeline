import argparse
import gzip
import zlib
import re
import os
from subprocess import check_call
from lxml import etree

from sgsession import Session


# The frame rate is the duration in whatever arbitrary base this is.
TIME_BASE = 254016000000

rate_names = {
    10584000000: '24',
    10594584000: '23.94',
    8467200000:  '30',
    8475667200:  '29.97',

}

parser = argparse.ArgumentParser()
parser.add_argument('-P', '--project', type=int, default=68) # Sandbox.
parser.add_argument('-p', '--parse-only', action='store_true')
parser.add_argument('-e', '--episode', required=True, type=int)
parser.add_argument('-n', '--dry-run', action='store_true')
parser.add_argument('prproj')
args = parser.parse_args()


class Element(etree.ElementBase):

    def __repr__(self):
        return '<%s %s %r>' % (self.tag, self.id, self.name)

    @property
    def id(self):
        return self.attrib.get('ObjectID') or self.attrib.get('ObjectUID')

    @property
    def name(self):
        node = self.find('Name')
        return None if node is None else node.text

    @property
    def ref_id(self):
        return self.attrib.get('ObjectRef') or self.attrib.get('ObjectURef')

    @property
    def ref(self):
        id_ = self.ref_id
        if id_:
            return by_id[id_]

def time_to_frame(time, base):
    frame = time / base
    assert float(frame) == float(time) / base
    return frame

def translate_path(path):
    path = path.replace('\\', '/')
    path = re.sub(r'^Y:/', '/Volumes/PD01/', path)
    path = re.sub(r'^Z:/', '/Volumes/AnimationProjects/', path)
    path = re.sub(r'^//10\.10\.1\.\d/pd01/', '/Volumes/PD01/', path)
    return os.path.normpath(path)

parser_lookup = etree.ElementDefaultClassLookup(element=Element)
parser = etree.XMLParser()
parser.set_element_class_lookup(parser_lookup)


unzipped = gzip.GzipFile(args.prproj, 'r')

tree = etree.parse(unzipped, parser)
root = tree.getroot()

by_id = {}
for node in root:
    id_ = node.attrib.get('ObjectID') or node.attrib.get('ObjectUID')
    if id_:
        by_id[id_] = node


footage_by_time = {}
metadata_by_time = {}
video_transitions = []

for seq in root.findall('Sequence'):

    print seq

    for track_group_ref in seq.findall('.//TrackGroup/Second'):
        track_group = track_group_ref.ref
        if track_group.tag != 'VideoTrackGroup':
            continue
        print track_group

        frame_rate = int(track_group.find('.//FrameRate').text)
        print '    rate: %-5s (%s)' % (rate_names.get(frame_rate, 'unknown'), frame_rate)

        for track_ref in track_group.findall('.//Track'):
            track = track_ref.ref
            print track

            for track_item_ref in track.findall('.//TrackItem'):
                track_item = track_item_ref.ref
                print track_item

                start_frame = time_to_frame(int(track_item.find('.//Start').text), frame_rate)
                end_frame   = time_to_frame(int(track_item.find('.//End'  ).text), frame_rate)
                time_key    = (start_frame, end_frame)
                print '   from', start_frame, 'to', end_frame

                if track_item.tag == 'VideoTransitionTrackItem':
                    video_transitions.append((start_frame, end_frame))
                    continue

                sub_clip = track_item.find('.//SubClip').ref
                print sub_clip

                #clip = sub_clip.find('Clip').ref
                #frame_rate = int(clip.find('.//FrameRate').text)
                #in_ = int(clip.find('.//InPoint').text)
                #out = int(clip.find('.//OutPoint').text)
                #print '    from', in_ / frame_rate, 'to', out / frame_rate

                master_clip = sub_clip.find('MasterClip').ref
                print master_clip

                for clip_ref in master_clip.findall('.//Clip'):
                    clip = clip_ref.ref
                    print clip


                    source = clip.find('.//Source').ref
                    print source

                    try:
                        media = source.find('.//Media').ref
                    except AttributeError:
                        continue
                    print media

                    path = media.find('FilePath').text
                    if path:
                        path = translate_path(path)
                        if os.path.exists(path):
                            footage_by_time.setdefault(time_key, []).append(path)
                    
                    prefs = media.find('ImporterPrefs')
                    if prefs is not None and prefs.text:

                        encoded = prefs.text
                        binary_struct = encoded.decode('base64')
                        try:
                            raw = binary_struct[32:].decode('zip')
                        except zlib.error:
                            print repr(binary_struct[:32])
                        else:
                            #xml = raw.decode('utf16')
                            subtitle_root = etree.fromstring(raw)
                            for str_node in subtitle_root.findall('.//TRString'):
                                metadata = str_node.text.strip() if str_node.text is not None else None
                                if metadata:
                                    print '    metadata:', repr(metadata)
                                    metadata_by_time.setdefault(time_key, []).append(metadata)

                print


    print


if args.parse_only:
    exit()  

# SHOTGUN PART

sg = Session()

project = {'type': 'Project', 'id': args.project} # Miao Miao
template = {'type': 'TaskTemplate', 'id': 8}

print 'Finding episode...'
episode = sg.find_one('$Episode', [
    ('code', 'starts_with', 'Episode_%02d_' % args.episode),
    ('project', 'is', project),
], ['code'])
print '   ', episode['code']

print 'Finding Shots...'
shots_by_edit_name = {}
for shot in sg.find('Shot', [
    ('sg_episode', 'is', episode),
], ['code', 'sg_cut_in', 'sg_cut_out', 'sg_editorial_name']):
    shots_by_edit_name[shot['sg_editorial_name']] = shot

for (start_frame, end_frame), footage_paths in sorted(footage_by_time.iteritems()):

    # Pick the best footage
    footage_paths = list(set(footage_paths))
    mov_path = next((path for path in footage_paths if path.lower().endswith('.mov')), None)
    avi_path = next((path for path in footage_paths if path.lower().endswith('.avi')), None)
    footage_path = mov_path or avi_path or footage_paths[0]

    metadatas = metadata_by_time.get((start_frame, end_frame))
    if not metadatas:
        for (meta_start, meta_end), metadatas in sorted(metadata_by_time.iteritems()):
            if start_frame == meta_start and end_frame < meta_end:
                print 'Footage ends early...'
                break
        else:
            print 'No metadata for footage:', footage_path
            continue

    for metadata in metadatas:
        m = re.match(r'^Sc(\d+)(-?[0-9a-zA-Z]+)?$', metadata)
        if m:
            break
    else:
        print '    metadata not recognized:', metadatas
        continue

    num, variant = m.groups()
    name = 'e%02d_sh%03d%s' % (args.episode, int(num), variant or '')
    print '%s (%s)' % (name, metadata)

    for t_start, t_end in video_transitions:
        if start_frame > t_start and start_frame <= t_end:
            print '    starts in transition'
            start_frame = t_start
        if end_frame >= t_start and end_frame < t_end:
            print '    ends in transition'
            end_frame = t_end

    print '   ', start_frame, 'to', end_frame, 
    print '   ', footage_path

    if args.dry_run:
        continue

    shot = shots_by_edit_name.get(metadata)

    if not shot:
        print 'Creating Shot...'
        shot = sg.create('Shot', {
            'project': project,
            'sg_episode': episode,
            'code': name,
            'sg_editorial_name': metadata,
            'sg_cut_in': start_frame,
            'sg_cut_out': end_frame - 1, # TODO: Assert this is correct.
            'sg_cut_duration': end_frame - start_frame,
            'task_template': template,
        })

    elif shot['code'] != name or shot['sg_cut_in'] != start_frame or shot['sg_cut_out'] != end_frame - 1:
        print 'Updating Shot...'
        sg.update('Shot', shot['id'], {
            'code': name,
            'sg_cut_in': start_frame,
            'sg_cut_out': end_frame - 1,
            'sg_cut_duration': end_frame - start_frame,
        })

    else:
        print 'Shot already exists:', shot

    if not os.path.exists(footage_path):
        continue

    versions = sg.find('Version', [('entity', 'is', shot)], ['sg_path_to_movie', 'sg_uploaded_movie'])
    version = next((v for v in versions if v['sg_path_to_movie'] == footage_path), None)

    version_name = os.path.splitext(os.path.basename(footage_path))[0]

    if not version:
        
        print 'Creating Version...'
        version = sg.create('Version', {
            'code': version_name,
            'entity': shot,
            'project': project,
            'sg_path_to_movie': footage_path,
        })

        print 'Updating Shot.latest_version...'
        sg.update('Shot', shot['id'], {'sg_latest_version': version})

    if not version.get('sg_uploaded_movie'):

        print 'Transcoding media:'
        print '   ', footage_path

        mp4_path = '/var/tmp/%s.%s.mp4' % (shot['code'], version_name)
        check_call([os.path.abspath(os.path.join(__file__, '..', 'transcode.sh')), footage_path, mp4_path])

        print 'Uploading media:'
        print '   ', mp4_path
        print '    %.2fMB' % (os.path.getsize(mp4_path) / 1024.0 / 1024)
        sg.upload('Version', version['id'], mp4_path, 'sg_uploaded_movie')

        os.unlink(mp4_path)

    # exit()

