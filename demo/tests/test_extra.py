from base64 import b64encode

from pytest_html import extras


def test_text(extra):
    extra.append(extras.text("Some simple Text", name="example_text"))


def test_html(extra):
    extra.append(extras.html("<div>Additional HTML</div>"))


def test_json(extra):
    extra.append(extras.json({"name": "pytest"}, name="example_JSON"))


def test_url(extra):
    extra.append(extras.url("http://www.example.com/", name="example_URL"))


def test_image(extra):
    image = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" width="120" height="90">
    <rect x="0" y="0" width="100%" height="100%"
          fill="red" stroke-width="0" />
    <text x="50%" y="50%" fill="black"
          text-anchor="middle" alignment-baseline="central">
        EXAMPLE
    </text>
</svg>"""
    extra.append(
        extras.svg(
            b64encode(image.encode("ascii")).decode("ascii"), name="example_image"
        )
    )
