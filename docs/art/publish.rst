
.. _publishing_artwork:

Publishing Artwork
==================

Abstract Pipeline
-----------------

Artwork working files are generally stored in the ``photoshop`` directory
of "art" tasks. Since multiple files are often reviewed together, they are
published as a unit with individual Version[s] created for each.

Concept Art
~~~~~~~~~~~

.. highlight:: shell

Batches of scans of concept are are generally placed into the following structure::

    $ART_TASK/
        photoshop/
            $SCAN_DATE/ # e.g.: 2017-02-09
                raw-scans/
                    # raw scans go here, e.g.:
                    char_art_001.tif
                # processed files go here, e.g.:
                char_art_001.jpg

They are generally published with the :ref:`publish-art <publish_art_command>` command,
with the publish named for the date of the scans, e.g.::

    publish-art --name 2017-02-09 /path/to/art.jpg /path/to/art-2.jpg


.. _publish_art_command:

The ``publish-art`` Command
---------------------------

The ``publish-art`` command was created to facilitate creating a single Publish
with a batch of concept artwork, and a Version for each piece of artwork.

It publishes the original artwork as-is, and also creates a "proxy" version: a
JPEG constrained to 2048px. That proxy is uploaded to Shotgun for review.

