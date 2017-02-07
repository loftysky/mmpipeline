from __future__ import absolute_import

import argparse
import json
import os
import subprocess
import sys

from sgpublish.commands.utils import add_publisher_arguments, extract_publisher_kwargs
from sgpublish.publisher import Publisher
from sgpublish.utils import basename
from sgpublish.versions import create_versions_for_publish


DIRECT_EXTS = set(('.jpg', '.jpeg', '.png'))
PROXIED_EXTS = set(('.psd', '.tif', '.tiff'))



def main(argv=None):

    parser = argparse.ArgumentParser()
    
    add_publisher_arguments(parser)
    parser.set_defaults(publisher_type='art')

    parser.add_argument('--no-promote', action='store_true')
    parser.add_argument('images', nargs='+',
        help='The images to publish.')

    args = parser.parse_args(argv)
    args.files = args.images # For laziness while developing.

    # Assert that all files are images we can handle.
    has_bad_image = False
    for path in args.files:
        ext = os.path.splitext(path)[1]
        if ext not in DIRECT_EXTS and ext not in PROXIED_EXTS:
            print >> sys.stderr, path, 'is not an image we can publish.'
            has_bad_image = True
    if has_bad_image:
        exit(1)

    # Pull the name/link from the first file by default.
    args.publisher_link = args.publisher_link or args.files[0]
    args.publisher_name = args.publisher_name or os.path.splitext(os.path.basename(args.files[0]))[0]

    kwargs = extract_publisher_kwargs(args)
    with Publisher(**kwargs) as publisher:

        proxy_dir = os.path.join(publisher.directory, 'proxies')
        os.makedirs(proxy_dir)

        image_paths = publisher.metadata['image_paths'] = []
        proxy_paths = publisher.metadata['proxy_paths'] = []

        for path in args.files:

            pub_path = publisher.add_file(path)
            image_paths.append(pub_path)

            basename, ext = os.path.splitext(os.path.basename(pub_path))
            proxy_path = publisher.unique_name(os.path.join(proxy_dir, basename + ext))

            # The first image is the "main" one.
            publisher.path = publisher.path or pub_path

            if ext in DIRECT_EXTS:
                data = json.loads(subprocess.check_output(['convert', path, 'json:-']))
                geo = data['image']['geometry']
                if geo['width'] > 2048 or geo['height'] > 2048:
                    print >> sys.stderr, 'Resizing', path
                    subprocess.check_call(['convert', path, '-resize', '2048x2048>', proxy_path])
                else:
                    publisher.add_file(path, proxy_path)
            elif ext in PROXIED_EXTS:
                proxy_path = publisher.unique_name(os.path.join(proxy_dir, basename + '.jpg'))
                print >> sys.stderr, 'Converting', path
                # The [0] flattens the image.
                subprocess.check_call(['convert', path + '[0]', '-resize', '2048x2048>', proxy_path])

            proxy_paths.append(proxy_path)

            # First proxy is the thumbnail.
            publisher.thumbnail_path = publisher.thumbnail_path or proxy_path


    if not args.no_promote:

        sg = publisher.sgfs.session

        for image_path, proxy_path in zip(image_paths, proxy_paths):
            basename = os.path.splitext(os.path.basename(image_path))[0]

            # We are about to do something a little silly. We set the path_to_frames
            # to be the proxy, JUST IN CASE our out-of-band Shotgun uploader
            # catches it first and starts uploading. Then we set it back.
            version = create_versions_for_publish(publisher.entity, [{
                'code': '%s - %s' % (publisher.name, basename),
                'description': publisher.description,
                'sg_path_to_frames': proxy_path,
            }], sgfs=publisher.sgfs)[0]

            print >> sys.stderr, 'Uploading', proxy_path
            sg.upload('Version', version['id'], proxy_path, 'sg_uploaded_movie', basename)

            sg.update('Version', version['id'], {
                'sg_path_to_frames': image_path,
            })


    print publisher.directory



if __name__ == '__main__':
    main()

