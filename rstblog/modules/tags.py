# -*- coding: utf-8 -*-
"""
    rstblog.modules.tags
    ~~~~~~~~~~~~~~~~~~~~

    Implements tagging.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from math import log
from urllib.parse import urljoin

from jinja2 import contextfunction

from werkzeug.contrib.atom import AtomFeed

from rstblog.signals import after_file_published, \
     before_build_finished


class Tag(object):

    def __init__(self, name, count):
        self.group = name[0].lower()
        self.name = name
        self.count = count


@contextfunction
def get_tags(context):
    tags = get_tag_summary(context['builder'])
    tags.sort(key=lambda x: x.name.lower())
    return tags


def get_tag_summary(builder):
    storage = builder.get_storage('tags')
    by_tag = storage.get('by_tag', {})
    result = []
    for tag, tagged in by_tag.items():
        result.append(Tag(tag, len(tagged)))
    result.sort(key=lambda x: x.count)
    return result


def get_tagged_entries(builder, tag):
    if isinstance(tag, Tag):
        tag = tag.name
    storage = builder.get_storage('tags')
    by_tag = storage.get('by_tag', {})
    return by_tag.get(tag) or []


def remember_tags(context):
    tags = context.config.merged_get('tags') or []
    storage = context.builder.get_storage('tags')
    by_file = storage.setdefault('by_file', {})
    by_file[context.source_filename] = tags
    by_tag = storage.setdefault('by_tag', {})
    for tag in tags:
        by_tag.setdefault(tag, []).append(context)
    context.tags = frozenset(tags)


def write_tags_page(builder):
    with builder.open_link_file('tags') as f:
        rv = builder.render_template('tags.html')
        f.write(rv + '\n')


def write_tag_feed(builder, tag):
    blog_author = builder.config.root_get('author')
    url = builder.config.root_get('canonical_url') or 'http://localhost/'
    name = builder.config.get('feed.name') or 'Recent Blog Posts'
    subtitle = builder.config.get('feed.subtitle') or 'Recent blog posts'
    feed = AtomFeed(name,
                    subtitle=subtitle,
                    feed_url=urljoin(url, builder.link_to('blog_feed')),
                    url=url)

    entries = get_tagged_entries(builder, tag)
    entries.sort(key=lambda x: x.pub_date, reverse=True)
    for entry in entries[:10]:
        feed.add(entry.title, str(entry.render_contents()),
                 content_type='html', author=blog_author,
                 url=urljoin(url, entry.slug),
                 updated=entry.pub_date)
    with builder.open_link_file('tagfeed', tag=tag.name) as f:
        f.write(feed.to_string() + '\n')


def write_tag_page(builder, tag):
    entries = get_tagged_entries(builder, tag)
    entries.sort(key=lambda x: x.pub_date, reverse=True)
    with builder.open_link_file('tag', tag=tag.name) as f:
        rv = builder.render_template('tag.html', {
            'tag':      tag,
            'entries':  entries
        })
        f.write(rv + '\n')


def write_tag_files(builder):
    write_tags_page(builder)
    for tag in get_tag_summary(builder):
        write_tag_page(builder, tag)
        write_tag_feed(builder, tag)


def setup(builder):
    after_file_published.connect(remember_tags)
    before_build_finished.connect(write_tag_files)
    builder.register_url('tag', config_key='modules.tags.tag_url',
                         config_default='/tags/<tag>/')
    builder.register_url('tagfeed', config_key='modules.tags.tag_feed_url',
                         config_default='/tags/<tag>/feed.atom')
    builder.register_url('tags', config_key='modules.tags.tags_url',
                         config_default='/tags/')
    builder.jinja_env.globals['get_tags'] = get_tags
