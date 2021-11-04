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

from pathlib import Path

from jinja2 import Template

import yaml


DEFAULT_THUMB_SIZE = 200

TEMPLATE = """
<ul class="thumbnails center" style="clear: both">
{% for item in images %}
    <li><a class="reference external image-reference" href="{{ item.full }}" title="{{ item.alt|escape }}"
        ><img
            width="{{ item.thumbnail_width }}"
            height="{{ item.thumbnail_height }}"
            alt="{{ item.alt|escape }}"
            src="{{ item.thumbnail }}"
        ></a></li>
{% endfor %}
</ul>
"""


class Gallery(Directive):
    option_spec = dict(thumbsize=directives.nonnegative_int,
                       square=directives.flag,
                       images=directives.path)

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False

    def __init__(self, *args, **kwargs):
        Directive.__init__(self, *args, **kwargs)
        self.template = Template(TEMPLATE)

    def run(self):
        size = self.options.get('thumbsize', DEFAULT_THUMB_SIZE)
        square = 'square' in self.options

        if 'images' in self.options:
            image_name = self.options.get('images')
            image_path = Path(directiveutils.get_document_dirname(self), image_name)
            with open(image_path) as f:
                yaml_content = f.read()
        else:
            yaml_content = '\n'.join(self.content)
        images = yaml.load(yaml_content)

        base_path = directiveutils.get_document_dirname(self)
        for image in images:
            thumbnail = utils.generate_thumbnail(base_path,
                                                 image['full'], size,
                                                 square=square)
            image['thumbnail'] = thumbnail.relpath
            image['thumbnail_width'] = thumbnail.width
            image['thumbnail_height'] = thumbnail.height

        html = self.template.render(images=images)
        return [nodes.raw('', html, format='html')]


def setup(builder):
    directives.register_directive('gallery', Gallery)
