import gzip
import zlib

from lxml import etree


'''
>>> b24 = 10584000000
>>> b30 = 8467200000
>>> b24 * 24 / b30
30

The frame rate is the duration in whatever arbitrary base this is.
One second is 254016000000:

>>> b30 * 30 == b24 * 24
True


'''

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


parser_lookup = etree.ElementDefaultClassLookup(element=Element)
parser = etree.XMLParser()
parser.set_element_class_lookup(parser_lookup)


unzipped = gzip.GzipFile('Scavenger_Hunt_edit.prproj', 'r')

tree = etree.parse(unzipped, parser)
root = tree.getroot()

by_id = {}
for node in root:
    id_ = node.attrib.get('ObjectID') or node.attrib.get('ObjectUID')
    if id_:
        by_id[id_] = node


for seq in root.findall('Sequence'):

    print seq

    for track_group_ref in seq.findall('.//TrackGroup/Second'):
        track_group = track_group_ref.ref
        if track_group.tag != 'VideoTrackGroup':
            continue
        print track_group

        frame_rate = int(track_group.find('.//FrameRate').text)

        for track_ref in track_group.findall('.//Track'):
            track = track_ref.ref
            print track

            for track_item_ref in track.findall('.//TrackItem'):
                track_item = track_item_ref.ref
                print track_item

                start = int(track_item.find('.//Start').text)
                end = int(track_item.find('.//End').text)
                print '   from', start / frame_rate, 'to', end / frame_rate

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

                    media = source.find('.//Media').ref
                    print media

                    path = media.find('FilePath').text
                    if path:
                        print '    path:', path
                    
                    prefs = media.find('ImporterPrefs')
                    if prefs is not None:

                        encoded = prefs.text
                        binary_struct = encoded.decode('base64')
                        try:
                            raw = binary_struct[32:].decode('zip')
                        except zlib.error:
                            print raw[:32]
                        else:
                            #xml = raw.decode('utf16')
                            subtitle_root = etree.fromstring(raw)
                            for str_node in subtitle_root.findall('.//TRString'):
                                print '    metadata:', str_node.text

                print


    print


