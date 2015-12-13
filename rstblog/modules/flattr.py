# -*- coding: utf-8 -*-
"""
    rstblog.modules.flattr
    ~~~~~~~~~~~~~~~~~~~~~~

    A tag which expands to a link to flattr content.

    Usage:

    .. flattr:: http://flattr.com/thing/registered/on/flattr

    :copyright: (c) 2012 by Aurélien Gâteau.
    :license: BSD, see LICENSE for more details.
"""



import os

from docutils import nodes
from docutils.parsers.rst import Directive, directives


class Flattr(Directive):
    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False

    def run(self):
        html = '<a href="%s" target="_blank"><img src="http://api.flattr.com/button/flattr-badge-large.png" alt="Flattr this" title="Flattr this" border="0" /></a>' % self.arguments[0]

        return [nodes.raw('', html, format='html')]


def setup(builder):
    directives.register_directive('flattr', Flattr)
