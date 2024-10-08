# -*- coding: utf-8 -*-
"""
    rstblog.modules.blog
    ~~~~~~~~~~~~~~~~~~~~

    The blog component.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""


from datetime import datetime
from urllib.parse import urljoin

from jinja2 import pass_context
from werkzeug.routing import Map, NotFound, Rule

from rstblog.signals import after_file_published, before_build_finished
from rstblog.utils import Pagination, fix_relative_urls, generate_feed_str


class YearArchive(object):
    def __init__(self, builder, year, entries):
        self.year = year
        self.entries = sorted(entries, key=lambda x: x.pub_date, reverse=True)
        self.count = len(entries)


def test_pattern(path, pattern):
    pattern = "/" + pattern.strip("/") + "/<path:extra>"
    adapter = Map([Rule(pattern)]).bind("dummy.invalid")
    try:
        endpoint, values = adapter.match(path.strip("/"))
    except NotFound:
        return
    return values["year"], values["month"], values["day"]


def process_blog_entry(context):
    if context.pub_date is None:
        pattern = context.config.get(
            "modules.blog.pub_date_match", "/<int:year>/<int:month>/<int:day>/"
        )
        if pattern is not None:
            rv = test_pattern(context.slug, pattern)
            if rv is not None:
                context.pub_date = datetime(*rv)

    if context.pub_date is not None and context.is_text:
        context.builder.get_storage("blog").setdefault(
            context.pub_date.year, []
        ).append(context)


def get_all_entries(builder):
    """Returns all blog entries in reverse order"""
    result = []
    storage = builder.get_storage("blog")
    for year, contexts in storage.items():
        result.extend(contexts)
    result.sort(key=lambda x: (x.pub_date, x.config.get("day-order", 0)), reverse=True)
    return result


def get_archive_summary(builder):
    """Returns a summary of the stuff in the archives."""
    storage = builder.get_storage("blog")
    years = list(storage.items())
    years.sort(key=lambda x: -x[0])
    return [YearArchive(builder, year, entries) for year, entries in years]


@pass_context
def get_recent_blog_entries(context, limit=10):
    return get_all_entries(context["builder"])[:limit]


def write_index_page(builder):
    use_pagination = builder.config.root_get("modules.blog.use_pagination", True)
    per_page = builder.config.root_get("modules.blog.per_page", 10)
    entries = get_all_entries(builder)
    pagination = Pagination(builder, entries, 1, per_page, "blog_index")
    while 1:
        with builder.open_link_file("blog_index", page=pagination.page) as f:
            rv = builder.render_template(
                "blog/index.html",
                {"pagination": pagination, "show_pagination": use_pagination},
            )
            f.write(rv + "\n")
            if not use_pagination or not pagination.has_next:
                break
            pagination = pagination.get_next()


def write_archive_pages(builder):
    archive = get_archive_summary(builder)
    with builder.open_link_file("blog_archive") as f:
        rv = builder.render_template("blog/archive.html", {"archive": archive})
        f.write(rv + "\n")


def write_feed(builder):
    title = builder.config.get("feed.name") or "Recent Blog Posts"
    entries = get_all_entries(builder)
    feed_path = builder.link_to("blog_feed")
    feed_str = generate_feed_str(builder, feed_path, title, entries)
    with builder.open_link_file("blog_feed") as f:
        f.write(feed_str)


def write_blog_files(builder):
    write_index_page(builder)
    write_archive_pages(builder)
    write_feed(builder)


def setup(builder):
    after_file_published.connect(process_blog_entry)
    before_build_finished.connect(write_blog_files)
    builder.register_url(
        "blog_index",
        config_key="modules.blog.index_url",
        config_default="/",
        defaults={"page": 1},
    )
    builder.register_url(
        "blog_index",
        config_key="modules.blog.paged_index_url",
        config_default="/page/<page>/",
    )
    builder.register_url(
        "blog_archive",
        config_key="modules.blog.archive_url",
        config_default="/archive/",
    )
    builder.register_url(
        "blog_feed", config_key="modules.blog.feed_url", config_default="/feed.atom"
    )
    builder.jinja_env.globals.update(get_recent_blog_entries=get_recent_blog_entries)
