"""
    rstblog.modules.directiveutils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Utilities to work with RST directives

    :copyright: (c) 2017 by Aurélien Gâteau.
    :license: BSD, see LICENSE for more details.
"""
import os


def get_document_dirname(directive):
    context = directive.state.document.settings.rstblog_context
    return os.path.dirname(context.full_source_filename)
