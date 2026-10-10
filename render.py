"""Markdown -> sanitized HTML rendering for MDBoard."""
import html
import re

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

# Fenced ```mermaid blocks are rendered client-side by mermaid.js (static/
# mermaid.min.js, doc.html). They are stashed out of the markdown pipeline
# before conversion and re-injected *after* bleach as
#     <div class="mermaid">html-escaped source</div>
# so the sanitizer never touches them and the browser gets the source back
# verbatim via textContent. Anything that is not a top-level ```mermaid
# fence (e.g. an indented one inside a list) falls through to codehilite.
_MERMAID_FENCE_RE = re.compile(
    r"^```mermaid[ \t]*\n(.*?)\n?```[ \t]*(?=$|\n)",
    re.DOTALL | re.MULTILINE,
)
_MERMAID_TOKEN = "MDBoardMermaidToken{}"


def _stash_mermaid(text):
    """Replace top-level ```mermaid fences with standalone placeholder
    paragraphs. Returns (prepared_markdown, [mermaid_source, ...])."""
    sources = []

    def _stash(match):
        sources.append(match.group(1).strip("\n"))
        # Surrounded by blank lines so markdown always wraps the token in its
        # own <p>, which _inject_mermaid later swaps for the mermaid div.
        return "\n\n" + _MERMAID_TOKEN.format(len(sources) - 1) + "\n\n"

    return _MERMAID_FENCE_RE.sub(_stash, text), sources


def _inject_mermaid(cleaned_html, sources):
    """Swap placeholder paragraphs for mermaid divs. Runs after bleach, so
    everything injected here is fully controlled: a fixed class attribute
    and an html-escaped text body."""
    for i, source in enumerate(sources):
        token = "<p>{}</p>".format(_MERMAID_TOKEN.format(i))
        if token in cleaned_html:
            cleaned_html = cleaned_html.replace(
                token,
                '<div class="mermaid">{}</div>'.format(html.escape(source)),
                1,
            )
    return cleaned_html


def render_markdown(text):
    prepared, mermaid_sources = _stash_mermaid(text or "")
    html = markdown.markdown(
        prepared,
        extensions=_EXTENSIONS,
        extension_configs=_EXT_CONFIGS,
        output_format="html5",
    )
    cleaned = bleach.clean(
        html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        protocols=["http", "https", "mailto"],
        strip=True,
    )
    return _inject_mermaid(cleaned, mermaid_sources)
