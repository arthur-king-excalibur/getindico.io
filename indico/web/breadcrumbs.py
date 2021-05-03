# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import render_template

from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.util import url_for_index


def render_breadcrumbs(*titles, category=None, event=None, management=False, category_url_factory=None):
    """Render the breadcrumb navigation.

    :param titles: A list of plain text titles.  If present, these will
                   simply create a unlinked trail of breadcrumbs.
                   A 'Home' element is inserted automatically.
    :param event: Generate the event/category breadcrumb trail starting
                  at the specified event.
    :param category: Generate the category breadcrumb trail starting at
                     the specified category.
    :param category_url_factory: Function to get the URL for a category
                                 breadcrumb. If missing, the standard
                                 category url will be used.
    :param management: Whether the event/category breadcrumb trail
                       should link to management pages.
    """
    assert titles or event or category
    if not category and not event:
        items = [(_('Home'), url_for_index())]
    else:
        items = []
        if event:
            items.append((event.title, url_for('event_management.settings', event) if management else event.url))
            category = event.category
        if category_url_factory is None:
            category_url_factory = lambda cat, management: (url_for('categories.manage_content', cat)
                                                            if management
                                                            else cat.url)
        for cat in category.chain_query[::-1]:
            items.append((cat.title, category_url_factory(cat, management=management)))
        items.reverse()
    items += [(x, None) if isinstance(x, str) else x for x in titles]
    return render_template('breadcrumbs.html', items=items, management=management)
