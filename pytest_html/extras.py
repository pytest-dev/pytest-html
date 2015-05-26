# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

FORMAT_HTML = 'html'
FORMAT_IMAGE = 'image'
FORMAT_JSON = 'json'
FORMAT_TEXT = 'text'
FORMAT_URL = 'url'


def extra(content, format, name=None):
    return {'name': name, 'format': format, 'content': content}


def html(content):
    return extra(content, FORMAT_HTML)


def image(content, name='Image'):
    return extra(content, FORMAT_IMAGE, name)


def json(content, name='JSON'):
    return extra(content, FORMAT_JSON, name)


def text(content, name='Text'):
    return extra(content, FORMAT_TEXT, name)


def url(content, name='URL'):
    return extra(content, FORMAT_URL, name)
