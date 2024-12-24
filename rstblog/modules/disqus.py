# -*- coding: utf-8 -*-
"""
rstblog.modules.disqus
~~~~~~~~~~~~~~~~~~~~~~

Implements disqus element if asked for.

To use this, include ``disqus`` in the list of modules in your ``config.yml`` file,
and add a configuration variable to match your settings : ``disqus.shortname``

To set developer mode on the site, set ``disqus.developer=1`` in your ``config.yml`` file.

To prevent comments on a particular page, set ``disqus = no`` in the page's YAML preamble.

:copyright: (c) 2012 by Martin Andrews.
:license: BSD, see LICENSE for more details.
"""

import urllib.parse

import jinja2


def disqus_vars_from_dict(dct):
    lst = []
    for key, value in sorted(list(dct.items())):
        if isinstance(value, int):
            value = str(value)
        elif isinstance(value, str):
            value = '"%s"' % jinja2.Markup(value).striptags().replace('"', r"\"")
        else:
            raise Exception("Unsupported type for disqus variable %s=%r" % (key, value))
        lst.append("var disqus_%s = %s;" % (key, value))
    return "\n".join(lst)


@jinja2.contextfunction
def get_disqus(context):
    config = context["builder"].config
    vars = dict()

    shortname = config.root_get("modules.disqus.shortname")
    if not shortname:
        raise Exception(
            'You must set the disqus shortname in "modules.disqus.shortname"'
        )
    vars["shortname"] = shortname

    if config.root_get("modules.disqus.developer", False):
        vars["developer"] = 1

    vars["url"] = (
        urllib.parse.urljoin(config.root_get("canonical_url"), context["ctx"].slug)
        + "/"
    )
    vars["title"] = context["ctx"].title

    disqus_txt = """
<div id="disqus_thread"></div>
<script type="text/javascript">
    %s

    /* * * DON'T EDIT BELOW THIS LINE * * */
    (function() {
        var dsq = document.createElement('script'); dsq.type = 'text/javascript'; dsq.async = true;
        dsq.src = 'http://' + disqus_shortname + '.disqus.com/embed.js';
        (document.getElementsByTagName('head')[0] || document.getElementsByTagName('body')[0]).appendChild(dsq);
    })();
</script>
<noscript>Please enable JavaScript to view the <a href="http://disqus.com/?ref_noscript">comments powered by Disqus.</a></noscript>
<a href="http://disqus.com" class="dsq-brlink">blog comments powered by <span class="logo-disqus">Disqus</span></a>
""" % disqus_vars_from_dict(vars)

    if not context["config"].get("disqus", True):
        disqus_txt = ""  # "<h1>DISQUS DEFEATED</h1>"

    return jinja2.Markup(disqus_txt)


def setup(builder):
    builder.jinja_env.globals["get_disqus"] = get_disqus
