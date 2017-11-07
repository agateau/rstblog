"""
    rstblog.modules.gallery
    ~~~~~~~~~~~~~~~~~~~~~~~

    Image gallery.

    :copyright: (c) 2017 by Aurélien Gâteau.
    :license: BSD, see LICENSE for more details.
"""
from rstblog import utils
from rstblog.modules import directiveutils

from docutils import nodes
from docutils.parsers.rst import Directive, directives

from jinja2 import Template

import yaml


DEFAULT_THUMB_SIZE = 200

TEMPLATE = """
<ul class="thumbnails center" style="clear: both">
{% for item in images %}
    <li><a class="reference external image-reference" href="{{ item.full }}" title="{{ item.alt }}"
        ><img
            width="{{ item.thumbnail_width }}"
            height="{{ item.thumbnail_height }}"
            alt="{{ item.alt }}"
            src="{{ item.thumbnail }}"
        ></a></li>
{% endfor %}
</ul>
"""


class Gallery(Directive):
    option_spec = dict(thumbsize=directives.nonnegative_int)

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False

    def __init__(self, *args, **kwargs):
        Directive.__init__(self, *args, **kwargs)
        self.template = Template(TEMPLATE)

    def run(self):
        size = self.options.get('thumbsize', DEFAULT_THUMB_SIZE)

        images = yaml.load('\n'.join(self.content))
        base_path = directiveutils.get_document_dirname(self)
        for image in images:
            thumbnail = utils.generate_thumbnail(base_path,
                                                 image['full'], size)
            image['thumbnail'] = thumbnail.relpath
            image['thumbnail_width'] = thumbnail.width
            image['thumbnail_height'] = thumbnail.height

        html = self.template.render(images=images)
        return [nodes.raw('', html, format='html')]


def setup(builder):
    directives.register_directive('gallery', Gallery)
