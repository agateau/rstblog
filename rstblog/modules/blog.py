"""
rstblog.modules.blog
~~~~~~~~~~~~~~~~~~~~

The blog component.

:copyright: (c) 2010 by Armin Ronacher.
:license: BSD, see LICENSE for more details.
"""

from datetime import datetime

from werkzeug.routing import Map, NotFound, Rule

from rstblog.signals import after_file_published, before_build_finished
from rstblog.utils import generate_feed_str


class YearArchive:
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


def get_archive_summary(builder) -> list[YearArchive]:
    """Returns a summary of the stuff in the archives."""
    storage = builder.get_storage("blog")
    years = list(storage.items())
    years.sort(key=lambda x: -x[0])
    return [YearArchive(builder, year, entries) for year, entries in years]


def write_archive_pages(builder):
    archive = get_archive_summary(builder)
    with builder.open_link_file("blog_archive") as f:
        rv = builder.render_template("blog/archive.html", {"archive": archive})
        f.write(rv + "\n")

    for year_archive in archive:
        with builder.open_link_file("blog_year_archive", year=year_archive.year) as f:
            rv = builder.render_template(
                "blog/year_archive.html", {"entry": year_archive}
            )
            f.write(rv + "\n")


def write_feed(builder):
    title = builder.config.get("feed.name") or "Recent Blog Posts"
    entries = get_all_entries(builder)
    feed_path = builder.link_to("blog_feed")
    feed_str = generate_feed_str(builder, feed_path, title, entries)
    with builder.open_link_file("blog_feed") as f:
        f.write(feed_str)


def write_blog_files(builder):
    write_archive_pages(builder)
    write_feed(builder)


def setup(builder):
    after_file_published.connect(process_blog_entry)
    before_build_finished.connect(write_blog_files)
    builder.register_url(
        "blog_archive",
        config_key="modules.blog.archive_url",
        config_default="/blog/",
    )
    builder.register_url(
        "blog_year_archive",
        config_key="modules.blog.archive_year_url",
        config_default="/blog/<year>/",
    )
    builder.register_url(
        "blog_feed", config_key="modules.blog.feed_url", config_default="/feed.atom"
    )
