# -*- coding: utf-8 -*-
"""
    rstblog.modules.thumbimg
    ~~~~~~~~~~~~~~~~~~~~~~~~

    An image tag with automatic thumbnails

    :copyright: (c) 2012 by Aurélien Gâteau.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import os

import PIL

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.images import Image

DEFAULT_THUMB_SIZE = 300

def need_update(dst, src):
    if not os.path.exists(dst):
        return True

    return os.path.getmtime(src) > os.path.getmtime(dst)


class ThumbImg(Image):
    option_spec = dict(Image.option_spec, **{"thumbsize": directives.nonnegative_int})

    def run(self):
        size = self.options.get("thumbsize", DEFAULT_THUMB_SIZE)

        big_filename = directives.uri(self.arguments[0])
        dirname, basename = os.path.split(big_filename)
        thumbnail_filename = os.path.join(dirname, "thumb_" + basename)

        self.generate_thumbnail(thumbnail_filename, big_filename, size)

        self.arguments[0] = thumbnail_filename
        self.options["target"] = big_filename
        return super(ThumbImg, self).run()

    def generate_thumbnail(self, thumbnail_filename, big_filename, size):
        context = self.state.document.settings.rstblog_context
        full_source_dirname = os.path.dirname(context.full_source_filename)

        full_thumbnail_filename = os.path.join(full_source_dirname, thumbnail_filename)
        full_big_filename = os.path.join(full_source_dirname, big_filename)

        if not need_update(full_thumbnail_filename, full_big_filename):
            return

        print "  Generating thumbnail for %s" % big_filename
        big_img = PIL.Image.open(full_big_filename)
        ratio = max(big_img.size) / float(size)
        thumbsize = [int(x/ratio) for x in big_img.size]
        thumb_img = big_img.resize(thumbsize, PIL.Image.BILINEAR)
        thumb_img.save(full_thumbnail_filename)


def setup(builder):
    directives.register_directive('thumbimg', ThumbImg)
