# -*- coding: utf-8 -*-
"""
    rstblog.programs
    ~~~~~~~~~~~~~~~~

    Builtin build programs.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import os
import shutil
import subprocess

from datetime import datetime
from io import StringIO
from weakref import ref

from rstblog.utils import fix_relative_urls, get_html_excerpt

import markdown
import yaml

from jinja2 import Environment, FileSystemLoader, Markup

class Program(object):

    def __init__(self, context):
        self._context = ref(context)

    @property
    def context(self):
        rv = self._context()
        if rv is None:
            raise RuntimeError('context went away, program is invalid')
        return rv

    def get_desired_filename(self):
        folder, basename = os.path.split(self.context.source_filename)
        simple_name = os.path.splitext(basename)[0]
        if simple_name == 'index':
            suffix = 'index.html'
        else:
            suffix = os.path.join(simple_name, 'index.html')
        return os.path.join(folder, suffix)

    def prepare(self):
        pass

    def render_contents(self):
        return ''

    def run(self):
        raise NotImplementedError()


class CopyProgram(Program):
    """A program that copies a file over unchanged"""

    def run(self):
        self.context.make_destination_folder()
        shutil.copy(self.context.full_source_filename,
                    self.context.full_destination_filename)

    def get_desired_filename(self):
        return self.context.source_filename


class SCSSProgram(Program):
    """A program that processes an SCSS file"""
    def run(self):
        self.context.make_destination_folder()
        subprocess.check_call(['sassc', '--sourcemap', '-t', 'compact',
                               self.context.full_source_filename,
                               self.context.full_destination_filename])

    def get_desired_filename(self):
        return self.context.source_filename.replace('scss', 'css')


class TemplatedProgram(Program):
    default_template = None

    def get_template_context(self):
        return {
            'url': self.context.url,
        }

    def run(self):
        template_name = self.context.config.get('template') \
            or self.default_template
        context = self.get_template_context()
        rv = self.context.render_template(template_name, context)
        with self.context.open_destination_file() as f:
            f.write(rv + '\n')

    def load_header(self, f):
        headers = ['---']
        while True:
            line = f.readline().rstrip()
            if not line:
                break
            headers.append(line)
        cfg = yaml.load(StringIO('\n'.join(headers)))
        if cfg and not isinstance(cfg, dict):
            raise ValueError('expected dict config in file "%s", got: %.40r' \
                % (self.context.source_filename, cfg))
        return cfg

    def process_header(self, cfg):
        self.context.config = self.context.config.add_from_dict(cfg)
        self.context.destination_filename = cfg.get(
            'destination_filename',
            self.context.destination_filename)

        pub_date_override = cfg.get('pub_date')
        if pub_date_override is not None:
            if not isinstance(pub_date_override, datetime):
                pub_date_override = datetime(pub_date_override.year,
                                             pub_date_override.month,
                                             pub_date_override.day)
            self.context.pub_date = pub_date_override

        self.context.summary = cfg.get('summary')


class HTMLProgram(TemplatedProgram):
    """A program that copies an HTML file unchanged, extracting its header"""
    default_template = 'rst_display.html'

    def prepare(self):
        with self.context.open_source_file() as f:
            cfg = self.load_header(f)
            self.context.html = f.read()

        if cfg:
            self.process_header(cfg)
            title = cfg.get('title')

        if title is not None:
            self.context.title = title

    def get_template_context(self):
        ctx = TemplatedProgram.get_template_context(self)
        ctx['rst'] = {
            'title': Markup(self.context.title).striptags(),
            'html_title': Markup('<h1>' + self.context.title + '</h1>'),
            'fragment': Markup(self.context.html),
        }
        return ctx

    def render_contents(self):
        return self.context.html


class RSTProgram(TemplatedProgram):
    """A program that renders an rst file into a template"""
    default_template = 'rst_display.html'

    def prepare(self):
        with self.context.open_source_file() as f:
            cfg = self.load_header(f)
            rst = f.read()
            rv = self.context.render_rst(rst)
            self.context.html = rv['fragment']
            title = rv['title']

        if cfg:
            self.process_header(cfg)
            title_override = cfg.get('title')
            if title_override is not None:
                title = title_override

        if title is not None:
            self.context.title = title

    def render_contents(self):
        return self.context.html

    def get_template_context(self):
        ctx = TemplatedProgram.get_template_context(self)
        ctx['rst'] = {
            'title': Markup(self.context.title).striptags(),
            'html_title': Markup('<h1>' + self.context.title + '</h1>'),
            'fragment': Markup(self.context.html),
        }
        return ctx


class MarkdownProgram(TemplatedProgram):
    """A program that renders a markdown file into a template"""
    default_template = 'rst_display.html'

    def prepare(self):
        with self.context.open_source_file() as f:
            cfg = self.load_header(f)
            md = f.read()
            md = self.process_embedded_rst_directives(md)
            html = markdown.markdown(md)

            html = fix_relative_urls('/', self.context.slug, html)
            self.context.html = html

            self.process_header(cfg)
            self.context.title = cfg.get('title')
            if self.context.summary is None:
                excerpt = get_html_excerpt(self.context.html)
                if excerpt:
                    self.context.summary = Markup(excerpt)

    def render_contents(self):
        return self.context.html

    def get_template_context(self):
        ctx = TemplatedProgram.get_template_context(self)
        ctx['rst'] = {
            'title': Markup(self.context.title).striptags(),
            'html_title': Markup('<h1>' + self.context.title + '</h1>'),
            'fragment': Markup(self.context.html),
        }
        return ctx


    def process_embedded_rst_directives(self, src):
        lst = []
        fl = StringIO(src)
        while True:
            line = fl.readline()
            if line == "":
                break
            if line.startswith(".."):
                rst_lst = [line]
                while True:
                    line = fl.readline()
                    if line.startswith(4 * " ") or line == "\n":
                        rst_lst.append(line)
                    else:
                        rst = "".join(rst_lst)
                        lst.append(self.process_rst_directive(rst))
                        lst.append("\n")

                        # The line we just read is not rst, don't forget to add it
                        lst.append(line)
                        break
            else:
                lst.append(line)
        return "".join(lst)

    def process_rst_directive(self, rst):
        rv = self.context.render_rst(rst)
        return rv['fragment']
