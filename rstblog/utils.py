# -*- coding: utf-8 -*-
"""
    rstblog.utils
    ~~~~~~~~~~~~~

    Various utilities.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import os
import re

from math import ceil
from urllib.parse import urlsplit, urljoin
from collections import namedtuple

import lxml.etree
import lxml.html

from markupsafe import Markup

from feedgen.feed import FeedGenerator

import PIL.Image

from bs4 import BeautifulSoup


class Pagination(object):
    """Internal helper class for paginations"""

    def __init__(self, builder, entries, page, per_page, url_key):
        self.builder = builder
        self.entries = entries
        self.page = page
        self.per_page = per_page
        self.url_key = url_key

    @property
    def total(self):
        return len(self.entries)

    @property
    def pages(self):
        return int(ceil(self.total / float(self.per_page)))

    def get_prev(self):
        return Pagination(self.builder, self.entries, self.page - 1,
                          self.per_page, self.url_key)

    @property
    def prev_num(self):
        """Number of the previous page."""
        return self.page - 1

    @property
    def has_prev(self):
        """True if a previous page exists"""
        return self.page > 1

    def get_next(self):
        return Pagination(self.builder, self.entries, self.page + 1,
                          self.per_page, self.url_key)

    @property
    def has_next(self):
        """True if a next page exists."""
        return self.page < self.pages

    @property
    def next_num(self):
        """Number of the next page"""
        return self.page + 1

    def get_slice(self):
        return self.entries[(self.page - 1) * self.per_page:
                            self.page * self.per_page]

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        """Iterates over the page numbers in the pagination.  The four
        parameters control the thresholds how many numbers should be produced
        from the sides.  Skipped page numbers are represented as `None`.
        """
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

    def __str__(self):
        return self.builder.render_template('_pagination.html', {
            'pagination':   self
        })

    def __html__(self):
        return Markup(str(self))


def fix_relative_url(base_url, slug, input_url):
    rv = urlsplit(input_url)
    if rv.netloc or rv.scheme:
        # Already absolute
        return input_url
    path = rv.path
    if path[0] != "/":
        path = os.path.normpath(os.path.join(slug, path))
    return urljoin(base_url, path)


def fix_relative_urls(base_url, slug, content):
    def process_elements(parent, tag, attribute):
        for element in parent.iter(tag):
            value = element.get(attribute)
            if not value:
                continue
            if value == '#':
                continue
            url = fix_relative_url(base_url, slug, value)
            element.set(attribute, url)

    root = lxml.html.fromstring(content)
    if len(root) == 0:
        return content
    process_elements(root, "img", "src")
    process_elements(root, "a", "href")
    process_elements(root, "video", "src")
    process_elements(root, "video", "poster")
    process_elements(root, "audio", "src")
    process_elements(root, "source", "src")
    html = lxml.etree.tostring(root).decode('utf-8')

    # Remove enclosing <div>, if any. It might not be there if the content is
    # only one paragraph.
    match = re.search("^<div>(.*)</div>$", html, re.DOTALL)
    if match:
        html = match.group(1)

    return html


def need_update(dst, src):
    """
    Returns true if file dst does not exist, or is older than src
    """
    if not os.path.exists(dst):
        return True
    return os.path.getmtime(src) > os.path.getmtime(dst)


Thumbnail = namedtuple("Thumbnail", ("relpath", "width", "height"))


def generate_thumbnail(base_path, image_relpath, size, square=False):
    """
    Generates or updates a thumbnail for an image at $base_path/$image_relpath.
    If `square` is True, crop the image in its center to produce a square
    thumbnail.
    Returns a Thumbnail
    """
    dirname, basename = os.path.split(image_relpath)
    thumbnail_relpath = os.path.join(dirname, 'thumb_' + basename)

    thumbnail_abspath = os.path.join(base_path, thumbnail_relpath)
    image_abspath = os.path.join(base_path, image_relpath)

    if need_update(thumbnail_abspath, image_abspath):
        print('  Generating thumbnail for {}'.format(image_relpath))
        big_img = PIL.Image.open(image_abspath)
        if square:
            ratio = min(big_img.size) / float(size)
            thumb_size = [int(x/ratio) for x in big_img.size]
            thumb_img = big_img.resize(thumb_size, PIL.Image.BILINEAR)
            padding = [(x - size) / 2 for x in thumb_img.size]
            thumb_img = thumb_img.crop((padding[0], padding[1],
                                       thumb_img.width - padding[0],
                                       thumb_img.height - padding[1]))
        else:
            ratio = max(big_img.size) / float(size)
            thumb_size = [int(x/ratio) for x in big_img.size]
            thumb_img = big_img.resize(thumb_size, PIL.Image.BILINEAR)
        thumb_img.save(thumbnail_abspath)
    else:
        thumb_img = PIL.Image.open(thumbnail_abspath)

    return Thumbnail(thumbnail_relpath, *thumb_img.size)


BREAK_COMMENT = '\n<!-- break -->\n'


def get_html_summary(content):
    """If content contains a BREAK_COMMENT returns the text before it,
    otherwise all the content"""
    lst = content.split(BREAK_COMMENT, 1)
    if len(lst) == 2:
        return lst[0].strip()
    else:
        return content


OgProperties = namedtuple("OgProperties", ("description", "image", "image_alt"))


def get_og_properties(html_content):
    """Returns on OgProperties for this html content.

    Uses the first <p> as description and the url of the first <img> as image.
    """
    if html_content is None:
        return None, None
    soup = BeautifulSoup(html_content, features="lxml")
    para = soup.find("p")
    if para:
        description = Markup(para).striptags()
    else:
        description = None
    image = soup.find("img")
    if image:
        url = image["src"]
        alt = image.get("alt")
    else:
        url = None
        alt = None
    return OgProperties(description, url, alt)


def generate_feed_str(builder, title, entries, subtitle=None):
    blog_author = builder.config.root_get('author')
    url = builder.config.root_get('canonical_url') or 'http://localhost/'
    feed_url = urljoin(url, builder.link_to('blog_feed'))
    subtitle = builder.config.get('feed.subtitle') or 'Recent blog posts'
    feed = FeedGenerator()
    feed.id(feed_url)
    feed.title(title)
    if subtitle:
        feed.subtitle(subtitle)
    feed.author(name=blog_author)
    feed.language('en')
    feed.link(href=url)
    feed.link(href=feed_url, rel='self')

    entries = sorted(entries, key=lambda x: x.pub_date, reverse=True)[:10]
    feed.updated(entries[0].pub_date.astimezone())

    for entry in entries:
        entry_url = urljoin(url, entry.slug)
        content = fix_relative_urls(url, entry.slug, entry.render_contents())
        categories = [{'term': x} for x in sorted(entry.tags)]
        pub_date = entry.pub_date.astimezone()

        feed_entry = feed.add_entry()
        feed_entry.id(entry_url)
        feed_entry.title(entry.title)
        feed_entry.link(href=entry_url, rel='self')
        feed_entry.published(pub_date)
        feed_entry.updated(pub_date)
        feed_entry.category(categories)
        feed_entry.content(content=content, type='html')

    return str(feed.atom_str(pretty=True), 'utf-8')
