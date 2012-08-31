# -*- coding: utf-8 -*-
"""
    rstblog.modules.thumbimg
    ~~~~~~~~~~~~~~~~~~~~~~~~

    An image tag with automatic thumbnails

    :copyright: (c) 2012 by Aurélien Gâteau.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.images import Image

class ThumbImg(Image):
    def run(self):
        reference = directives.uri(self.arguments[0])
        self.arguments[0] = "thumb_" + self.arguments[0]
        self.options["target"] = reference
        return super(ThumbImg, self).run()

def setup(builder):
    directives.register_directive('thumbimg', ThumbImg)
