"""Markdown -> sanitized HTML rendering for MDBoard."""
import markdown
import bleach

_EXTENSIONS = ["fenced_code", "codehilite", "tables", "sane_lists", "nl2br", "toc"]
_EXT_CONFIGS = {"codehilite": {"guess_lang": False, "css_class": "codehilite"}}

# Allowlist: standard markdown output + codehilite's div/pre/span/class.
_ALLOWED_TAGS = [
    "h1", "h2", "h3", "h4", "h5", "h6", "p", "br", "hr",
    "pre", "code", "span", "div",
    "a", "img", "strong", "em", "b", "i", "del", "ins", "sub", "sup",
    "blockquote", "ul", "ol", "li",
    "table", "thead", "tbody", "tr", "th", "td", "caption",
]
_ALLOWED_ATTRS = {
    "*": ["class", "id"],
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title"],
}

def render_markdown(text):
    html = markdown.markdown(
        text or "",
        extensions=_EXTENSIONS,
        extension_configs=_EXT_CONFIGS,
        output_format="html5",
    )
    return bleach.clean(
        html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        protocols=["http", "https", "mailto"],
        strip=True,
    )
