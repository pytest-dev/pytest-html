# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from typing import Optional

FORMAT_HTML = "html"
FORMAT_IMAGE = "image"
FORMAT_JSON = "json"
FORMAT_TEXT = "text"
FORMAT_URL = "url"
FORMAT_VIDEO = "video"


def extra(
    content: str,
    format_type: str,
    name: Optional[str] = None,
    mime_type: Optional[str] = None,
    extension: Optional[str] = None,
) -> dict[str, Optional[str]]:
    return {
        "name": name,
        "format_type": format_type,
        "content": content,
        "mime_type": mime_type,
        "extension": extension,
    }


def html(content: str) -> dict[str, Optional[str]]:
    return extra(content, FORMAT_HTML)


def image(
    content: str,
    name: str = "Image",
    mime_type: str = "image/png",
    extension: str = "png",
) -> dict[str, Optional[str]]:
    return extra(content, FORMAT_IMAGE, name, mime_type, extension)


def png(content: str, name: str = "Image") -> dict[str, Optional[str]]:
    return image(content, name, mime_type="image/png", extension="png")


def jpg(content: str, name: str = "Image") -> dict[str, Optional[str]]:
    return image(content, name, mime_type="image/jpeg", extension="jpg")


def svg(content: str, name: str = "Image") -> dict[str, Optional[str]]:
    return image(content, name, mime_type="image/svg+xml", extension="svg")


def json(content: str, name: str = "JSON") -> dict[str, Optional[str]]:
    return extra(content, FORMAT_JSON, name, "application/json", "json")


def text(content: str, name: str = "Text") -> dict[str, Optional[str]]:
    return extra(content, FORMAT_TEXT, name, "text/plain", "txt")


def url(content: str, name: str = "URL") -> dict[str, Optional[str]]:
    return extra(content, FORMAT_URL, name)


def video(
    content: str,
    name: str = "Video",
    mime_type: str = "video/mp4",
    extension: str = "mp4",
) -> dict[str, Optional[str]]:
    return extra(content, FORMAT_VIDEO, name, mime_type, extension)


def mp4(content: str, name: str = "Video") -> dict[str, Optional[str]]:
    return video(content, name)
