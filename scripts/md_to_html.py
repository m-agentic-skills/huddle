#!/usr/bin/env python3
"""Convert a Markdown file to a self-contained HTML page styled like GitHub."""

import sys
import os

try:
    import mistune
    from mistune.plugins import table, footnotes, formatting
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, TextLexer
    from pygments.formatters import HtmlFormatter
    from pygments.util import ClassNotFound
except ImportError as e:
    sys.exit(f"Missing dependency: {e}\nRun: pip install mistune pygments")


# ---------------------------------------------------------------------------
# Syntax-highlighted code renderer
# ---------------------------------------------------------------------------

class HighlightRenderer(mistune.HTMLRenderer):
    def block_code(self, code, **attrs):
        lang = (attrs or {}).get("info", "") or ""
        lang = lang.strip().split()[0] if lang.strip() else ""
        try:
            lexer = get_lexer_by_name(lang) if lang else TextLexer()
        except ClassNotFound:
            lexer = TextLexer()
        formatter = HtmlFormatter(nowrap=True)
        highlighted = highlight(code, lexer, formatter)
        lang_attr = f' class="language-{lang}"' if lang else ""
        return f'<pre><code{lang_attr}>{highlighted}</code></pre>\n'


# ---------------------------------------------------------------------------
# Markdown → HTML body
# ---------------------------------------------------------------------------

def build_markdown():
    renderer = HighlightRenderer(escape=False)
    return mistune.create_markdown(
        renderer=renderer,
        plugins=[
            "strikethrough",
            "table",
            "task_lists",
            "footnotes",
            "def_list",
            "abbr",
            "mark",
            "superscript",
            "subscript",
        ],
    )


# ---------------------------------------------------------------------------
# GitHub-flavored CSS (self-contained, no external requests)
# ---------------------------------------------------------------------------

PYGMENTS_CSS = HtmlFormatter().get_style_defs(".highlight")

GITHUB_CSS = """
*, *::before, *::after { box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial,
               sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
  font-size: 16px;
  line-height: 1.5;
  color: #1f2328;
  background-color: #ffffff;
  margin: 0;
  padding: 0;
}

.markdown-body {
  max-width: 980px;
  margin: 0 auto;
  padding: 45px;
}

@media (max-width: 767px) {
  .markdown-body { padding: 15px; }
}

/* Headings */
.markdown-body h1, .markdown-body h2 {
  padding-bottom: .3em;
  border-bottom: 1px solid #d1d9e0b3;
}
.markdown-body h1 { font-size: 2em;   margin: .67em 0; }
.markdown-body h2 { font-size: 1.5em; margin: 1.2em 0 .6em; }
.markdown-body h3 { font-size: 1.25em; }
.markdown-body h4 { font-size: 1em; }
.markdown-body h5 { font-size: .875em; }
.markdown-body h6 { font-size: .85em; color: #636c76; }
.markdown-body h1,h2,h3,h4,h5,h6 { font-weight: 600; line-height: 1.25; margin-top: 24px; margin-bottom: 16px; }

/* Paragraphs & spacing */
.markdown-body p, .markdown-body blockquote, .markdown-body ul, .markdown-body ol,
.markdown-body dl, .markdown-body table, .markdown-body pre, .markdown-body details {
  margin-top: 0;
  margin-bottom: 16px;
}

/* Links */
.markdown-body a { color: #0969da; text-decoration: none; }
.markdown-body a:hover { text-decoration: underline; }

/* Code */
.markdown-body code {
  font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas,
               "Liberation Mono", monospace;
  font-size: 85%;
  background-color: #afb8c133;
  padding: .2em .4em;
  border-radius: 6px;
}
.markdown-body pre {
  background-color: #f6f8fa;
  border-radius: 6px;
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
}
.markdown-body pre code {
  background: transparent;
  padding: 0;
  font-size: inherit;
  white-space: pre;
  border: 0;
}

/* Blockquote */
.markdown-body blockquote {
  color: #636c76;
  border-left: .25em solid #d1d9e0;
  padding: 0 1em;
  margin-left: 0;
}

/* Tables */
.markdown-body table {
  border-spacing: 0;
  border-collapse: collapse;
  width: max-content;
  max-width: 100%;
  overflow: auto;
}
.markdown-body table th, .markdown-body table td {
  padding: 6px 13px;
  border: 1px solid #d1d9e0;
}
.markdown-body table th { font-weight: 600; background-color: #f6f8fa; }
.markdown-body table tr { background-color: #ffffff; border-top: 1px solid #d1d9e0b3; }
.markdown-body table tr:nth-child(2n) { background-color: #f6f8fa; }

/* Lists */
.markdown-body ul, .markdown-body ol { padding-left: 2em; }
.markdown-body li + li { margin-top: .25em; }

/* Task lists */
.markdown-body .task-list-item { list-style-type: none; }
.markdown-body .task-list-item input[type=checkbox] {
  margin: 0 .2em .25em -1.4em;
  vertical-align: middle;
}

/* Horizontal rule */
.markdown-body hr {
  height: .25em;
  padding: 0;
  margin: 24px 0;
  background-color: #d1d9e0;
  border: 0;
}

/* Images */
.markdown-body img { max-width: 100%; }

/* Footnotes */
.markdown-body .footnotes { font-size: 85%; color: #636c76; border-top: 1px solid #d1d9e0; margin-top: 2em; padding-top: 1em; }

/* Definition lists */
.markdown-body dt { font-weight: 600; }
.markdown-body dd { margin-left: 1.5em; margin-bottom: .5em; }

/* Mark / highlight */
.markdown-body mark { background-color: #fff8c5; border-radius: 3px; padding: .1em .2em; }

/* Details / summary */
.markdown-body details summary { cursor: pointer; font-weight: 600; }
"""


# ---------------------------------------------------------------------------
# Full HTML wrapper
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
{github_css}
  </style>
  <style>
/* Pygments syntax highlighting */
.highlight {{ background: transparent; }}
{pygments_css}
  </style>
</head>
<body>
  <article class="markdown-body">
{body}
  </article>
</body>
</html>
"""


def convert(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()

    md = build_markdown()
    body = md(text)
    title = os.path.basename(md_path)

    return HTML_TEMPLATE.format(
        title=title,
        github_css=GITHUB_CSS,
        pygments_css=PYGMENTS_CSS,
        body=body,
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.md> [output.html]", file=sys.stderr)
        sys.exit(1)

    html = convert(sys.argv[1])

    if len(sys.argv) >= 3:
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Written to {sys.argv[2]}")
    else:
        print(html)
