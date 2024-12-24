# -*- coding: utf-8 -*-
"""
rstblog.modules.thumbimg
~~~~~~~~~~~~~~~~~~~~~~~~

An image tag with automatic thumbnails

:copyright: (c) 2012 by Aurélien Gâteau.
:license: BSD, see LICENSE for more details.
"""

from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.images import Image

from rstblog import utils
from rstblog.modules import directiveutils

DEFAULT_THUMB_SIZE = 300


class ThumbImg(Image):
    option_spec = dict(Image.option_spec, **{"thumbsize": directives.nonnegative_int})

    def run(self):
        size = self.options.get("thumbsize", DEFAULT_THUMB_SIZE)

        big_filename = directives.uri(self.arguments[0])
        document_dirname = directiveutils.get_document_dirname(self)
        thumbnail = utils.generate_thumbnail(document_dirname, big_filename, size)

        self.arguments[0] = thumbnail.relpath
        self.options["target"] = big_filename
        return super(ThumbImg, self).run()


def setup(builder):
    directives.register_directive("thumbimg", ThumbImg)
