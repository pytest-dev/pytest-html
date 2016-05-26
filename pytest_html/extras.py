# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

FORMAT_HTML = 'html'
FORMAT_IMAGE = 'image'
FORMAT_JSON = 'json'
FORMAT_TEXT = 'text'
FORMAT_URL = 'url'


def extra(content, format_, column, name=None):
    return {'name': name, 'format': format_, 'content': content, 'column': column}


def html(content, column='Links', name=None):
    return extra(content, FORMAT_HTML, column, name)


def image(content, column='Links', name='Image'):
    return extra(content, FORMAT_IMAGE, column, name)


def json(content, column='Links', name='JSON'):
    return extra(content, FORMAT_JSON, column, name)


def text(content, column='Links', name='Text'):
    return extra(content, FORMAT_TEXT, column, name)


def url(content, column='Links', name='URL'):
    return extra(content, FORMAT_URL, column, name)
