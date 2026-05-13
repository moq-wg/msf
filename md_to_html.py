#!/usr/bin/env python3
"""
Markdown to HTML Converter

Converts markdown documents to beautifully styled HTML with:
- Syntax highlighting for code blocks
- Table of contents generation
- Dark/light theme support
- Responsive design
- Print-friendly styling

Usage:
    python md_to_html.py [input.md] [output.html]
    python md_to_html.py  # Uses defaults: TECHNICAL_ARCHITECTURE.md -> TECHNICAL_ARCHITECTURE.html

Requirements:
    pip install markdown pygments

Author: CIH Documentation Team
Date: January 2025
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

try:
    import markdown
    from markdown.extensions.codehilite import CodeHiliteExtension
    from markdown.extensions.tables import TableExtension
    from markdown.extensions.toc import TocExtension
    from markdown.extensions.fenced_code import FencedCodeExtension
    from markdown.extensions.attr_list import AttrListExtension
except ImportError:
    print("Required packages not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "markdown", "pygments"])
    import markdown
    from markdown.extensions.codehilite import CodeHiliteExtension
    from markdown.extensions.tables import TableExtension
    from markdown.extensions.toc import TocExtension
    from markdown.extensions.fenced_code import FencedCodeExtension
    from markdown.extensions.attr_list import AttrListExtension


# HTML Template with embedded CSS
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        /* CSS Variables for theming */
        :root {{
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --bg-tertiary: #0f3460;
            --bg-code: #0d1117;
            --text-primary: #e4e4e7;
            --text-secondary: #a1a1aa;
            --text-muted: #71717a;
            --accent-primary: #3b82f6;
            --accent-secondary: #8b5cf6;
            --accent-success: #22c55e;
            --accent-warning: #f59e0b;
            --accent-error: #ef4444;
            --border-color: #27272a;
            --table-border: #3f3f46;
            --table-header-bg: #27272a;
            --table-row-hover: #1f1f23;
            --link-color: #60a5fa;
            --link-hover: #93c5fd;
            --scrollbar-bg: #27272a;
            --scrollbar-thumb: #52525b;
        }}

        /* Light theme */
        [data-theme="light"] {{
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --bg-tertiary: #f1f5f9;
            --bg-code: #f6f8fa;
            --text-primary: #18181b;
            --text-secondary: #3f3f46;
            --text-muted: #71717a;
            --border-color: #e4e4e7;
            --table-border: #d4d4d8;
            --table-header-bg: #f4f4f5;
            --table-row-hover: #fafafa;
            --link-color: #2563eb;
            --link-hover: #1d4ed8;
            --scrollbar-bg: #e4e4e7;
            --scrollbar-thumb: #a1a1aa;
        }}

        /* Base styles */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        html {{
            scroll-behavior: smooth;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.7;
            font-size: 16px;
        }}

        /* Scrollbar styling */
        ::-webkit-scrollbar {{
            width: 10px;
            height: 10px;
        }}

        ::-webkit-scrollbar-track {{
            background: var(--scrollbar-bg);
        }}

        ::-webkit-scrollbar-thumb {{
            background: var(--scrollbar-thumb);
            border-radius: 5px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: var(--text-muted);
        }}

        /* Layout */
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}

        /* Header */
        .header {{
            position: sticky;
            top: 0;
            z-index: 100;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            backdrop-filter: blur(10px);
        }}

        .header h1 {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
        }}

        .header-controls {{
            display: flex;
            gap: 1rem;
            align-items: center;
        }}

        /* Theme toggle button */
        .theme-toggle {{
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.875rem;
            transition: all 0.2s ease;
        }}

        .theme-toggle:hover {{
            background: var(--accent-primary);
            color: white;
        }}

        /* Print button */
        .print-btn {{
            background: var(--accent-primary);
            border: none;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.875rem;
            transition: all 0.2s ease;
        }}

        .print-btn:hover {{
            background: var(--accent-secondary);
        }}

        /* Main content area */
        .main-content {{
            display: flex;
            gap: 2rem;
        }}

        /* Sidebar / Table of Contents */
        .sidebar {{
            position: sticky;
            top: 80px;
            width: 280px;
            max-height: calc(100vh - 100px);
            overflow-y: auto;
            flex-shrink: 0;
            padding-right: 1rem;
        }}

        .toc {{
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
        }}

        .toc-title {{
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 1rem;
        }}

        .toc ul {{
            list-style: none;
        }}

        .toc li {{
            margin: 0.5rem 0;
        }}

        .toc a {{
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.875rem;
            display: block;
            padding: 0.25rem 0;
            transition: color 0.2s ease;
        }}

        .toc a:hover {{
            color: var(--accent-primary);
        }}

        .toc ul ul {{
            margin-left: 1rem;
        }}

        .toc ul ul a {{
            font-size: 0.8125rem;
            color: var(--text-muted);
        }}

        /* Article content */
        .content {{
            flex: 1;
            min-width: 0;
        }}

        .content > * {{
            margin-bottom: 1.5rem;
        }}

        /* Typography */
        h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-top: 3rem;
            margin-bottom: 1.5rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid var(--accent-primary);
            color: var(--text-primary);
        }}

        h2 {{
            font-size: 1.875rem;
            font-weight: 600;
            margin-top: 2.5rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border-color);
            color: var(--text-primary);
        }}

        h3 {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-top: 2rem;
            margin-bottom: 0.75rem;
            color: var(--text-primary);
        }}

        h4 {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-top: 1.5rem;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }}

        h5 {{
            font-size: 1.125rem;
            font-weight: 600;
            margin-top: 1.25rem;
            margin-bottom: 0.5rem;
            color: var(--text-secondary);
        }}

        h6 {{
            font-size: 1rem;
            font-weight: 600;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
            color: var(--text-muted);
        }}

        p {{
            color: var(--text-secondary);
            margin-bottom: 1rem;
        }}

        /* Links */
        a {{
            color: var(--link-color);
            text-decoration: none;
            transition: color 0.2s ease;
        }}

        a:hover {{
            color: var(--link-hover);
            text-decoration: underline;
        }}

        /* Lists */
        ul, ol {{
            margin: 1rem 0;
            padding-left: 1.5rem;
            color: var(--text-secondary);
        }}

        li {{
            margin: 0.5rem 0;
        }}

        li::marker {{
            color: var(--accent-primary);
        }}

        /* Code blocks */
        pre {{
            background: var(--bg-code);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            overflow-x: auto;
            margin: 1.5rem 0;
        }}

        pre code {{
            font-family: 'SF Mono', 'Fira Code', 'Monaco', 'Consolas', monospace;
            font-size: 0.875rem;
            line-height: 1.6;
            color: var(--text-primary);
            background: transparent;
            padding: 0;
        }}

        /* Inline code */
        code {{
            font-family: 'SF Mono', 'Fira Code', 'Monaco', 'Consolas', monospace;
            font-size: 0.875em;
            background: var(--bg-tertiary);
            color: var(--accent-warning);
            padding: 0.2em 0.4em;
            border-radius: 4px;
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1.5rem 0;
            font-size: 0.9375rem;
        }}

        thead {{
            background: var(--table-header-bg);
        }}

        th {{
            text-align: left;
            padding: 0.75rem 1rem;
            font-weight: 600;
            color: var(--text-primary);
            border: 1px solid var(--table-border);
        }}

        td {{
            padding: 0.75rem 1rem;
            border: 1px solid var(--table-border);
            color: var(--text-secondary);
        }}

        tbody tr:hover {{
            background: var(--table-row-hover);
        }}

        /* Blockquotes */
        blockquote {{
            border-left: 4px solid var(--accent-primary);
            background: var(--bg-secondary);
            margin: 1.5rem 0;
            padding: 1rem 1.5rem;
            border-radius: 0 8px 8px 0;
        }}

        blockquote p {{
            color: var(--text-secondary);
            margin: 0;
        }}

        /* Horizontal rules */
        hr {{
            border: none;
            border-top: 1px solid var(--border-color);
            margin: 3rem 0;
        }}

        /* Strong and emphasis */
        strong {{
            font-weight: 600;
            color: var(--text-primary);
        }}

        em {{
            font-style: italic;
        }}

        /* Images */
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 1.5rem 0;
        }}

        /* Definition lists */
        dl {{
            margin: 1rem 0;
        }}

        dt {{
            font-weight: 600;
            color: var(--text-primary);
            margin-top: 1rem;
        }}

        dd {{
            margin-left: 1.5rem;
            color: var(--text-secondary);
        }}

        /* Syntax highlighting (Pygments) */
        .codehilite {{
            background: var(--bg-code);
            border-radius: 8px;
            overflow: hidden;
        }}

        .codehilite pre {{
            margin: 0;
            border: none;
        }}

        /* Pygments syntax colors */
        .codehilite .hll {{ background-color: #3c3836 }}
        .codehilite .c {{ color: #928374; font-style: italic }} /* Comment */
        .codehilite .k {{ color: #fb4934 }} /* Keyword */
        .codehilite .o {{ color: #fe8019 }} /* Operator */
        .codehilite .cm {{ color: #928374; font-style: italic }} /* Comment.Multiline */
        .codehilite .cp {{ color: #8ec07c }} /* Comment.Preproc */
        .codehilite .c1 {{ color: #928374; font-style: italic }} /* Comment.Single */
        .codehilite .cs {{ color: #928374; font-weight: bold; font-style: italic }} /* Comment.Special */
        .codehilite .gd {{ color: #fb4934 }} /* Generic.Deleted */
        .codehilite .ge {{ font-style: italic }} /* Generic.Emph */
        .codehilite .gr {{ color: #fb4934 }} /* Generic.Error */
        .codehilite .gh {{ color: #b8bb26; font-weight: bold }} /* Generic.Heading */
        .codehilite .gi {{ color: #b8bb26 }} /* Generic.Inserted */
        .codehilite .go {{ color: #928374 }} /* Generic.Output */
        .codehilite .gp {{ color: #fabd2f }} /* Generic.Prompt */
        .codehilite .gs {{ font-weight: bold }} /* Generic.Strong */
        .codehilite .gu {{ color: #b8bb26; font-weight: bold }} /* Generic.Subheading */
        .codehilite .gt {{ color: #fb4934 }} /* Generic.Traceback */
        .codehilite .kc {{ color: #fb4934 }} /* Keyword.Constant */
        .codehilite .kd {{ color: #fb4934 }} /* Keyword.Declaration */
        .codehilite .kn {{ color: #fb4934 }} /* Keyword.Namespace */
        .codehilite .kp {{ color: #fb4934 }} /* Keyword.Pseudo */
        .codehilite .kr {{ color: #fb4934 }} /* Keyword.Reserved */
        .codehilite .kt {{ color: #fabd2f }} /* Keyword.Type */
        .codehilite .m {{ color: #d3869b }} /* Literal.Number */
        .codehilite .s {{ color: #b8bb26 }} /* Literal.String */
        .codehilite .na {{ color: #b8bb26 }} /* Name.Attribute */
        .codehilite .nb {{ color: #fabd2f }} /* Name.Builtin */
        .codehilite .nc {{ color: #fabd2f }} /* Name.Class */
        .codehilite .no {{ color: #d3869b }} /* Name.Constant */
        .codehilite .nd {{ color: #8ec07c }} /* Name.Decorator */
        .codehilite .ni {{ color: #fabd2f }} /* Name.Entity */
        .codehilite .ne {{ color: #fb4934 }} /* Name.Exception */
        .codehilite .nf {{ color: #fabd2f }} /* Name.Function */
        .codehilite .nl {{ color: #fabd2f }} /* Name.Label */
        .codehilite .nn {{ color: #ebdbb2 }} /* Name.Namespace */
        .codehilite .nt {{ color: #fb4934 }} /* Name.Tag */
        .codehilite .nv {{ color: #ebdbb2 }} /* Name.Variable */
        .codehilite .ow {{ color: #fe8019 }} /* Operator.Word */
        .codehilite .w {{ color: #ebdbb2 }} /* Text.Whitespace */
        .codehilite .mb {{ color: #d3869b }} /* Literal.Number.Bin */
        .codehilite .mf {{ color: #d3869b }} /* Literal.Number.Float */
        .codehilite .mh {{ color: #d3869b }} /* Literal.Number.Hex */
        .codehilite .mi {{ color: #d3869b }} /* Literal.Number.Integer */
        .codehilite .mo {{ color: #d3869b }} /* Literal.Number.Oct */
        .codehilite .sb {{ color: #b8bb26 }} /* Literal.String.Backtick */
        .codehilite .sc {{ color: #b8bb26 }} /* Literal.String.Char */
        .codehilite .sd {{ color: #b8bb26 }} /* Literal.String.Doc */
        .codehilite .s2 {{ color: #b8bb26 }} /* Literal.String.Double */
        .codehilite .se {{ color: #fe8019 }} /* Literal.String.Escape */
        .codehilite .sh {{ color: #b8bb26 }} /* Literal.String.Heredoc */
        .codehilite .si {{ color: #b8bb26 }} /* Literal.String.Interpol */
        .codehilite .sx {{ color: #b8bb26 }} /* Literal.String.Other */
        .codehilite .sr {{ color: #b8bb26 }} /* Literal.String.Regex */
        .codehilite .s1 {{ color: #b8bb26 }} /* Literal.String.Single */
        .codehilite .ss {{ color: #83a598 }} /* Literal.String.Symbol */
        .codehilite .bp {{ color: #fabd2f }} /* Name.Builtin.Pseudo */
        .codehilite .vc {{ color: #ebdbb2 }} /* Name.Variable.Class */
        .codehilite .vg {{ color: #ebdbb2 }} /* Name.Variable.Global */
        .codehilite .vi {{ color: #ebdbb2 }} /* Name.Variable.Instance */
        .codehilite .il {{ color: #d3869b }} /* Literal.Number.Integer.Long */

        /* Document info box */
        .doc-info {{
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
            margin: 2rem 0;
        }}

        .doc-info h3 {{
            margin-top: 0;
            color: var(--accent-primary);
        }}

        /* Back to top button */
        .back-to-top {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: var(--accent-primary);
            color: white;
            border: none;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
            font-size: 0.875rem;
        }}

        .back-to-top.visible {{
            opacity: 1;
            visibility: visible;
        }}

        .back-to-top:hover {{
            background: var(--accent-secondary);
            transform: translateY(-2px);
        }}

        /* Footer */
        .footer {{
            margin-top: 4rem;
            padding: 2rem;
            border-top: 1px solid var(--border-color);
            text-align: center;
            color: var(--text-muted);
            font-size: 0.875rem;
        }}

        /* Responsive design */
        @media (max-width: 1024px) {{
            .main-content {{
                flex-direction: column;
            }}

            .sidebar {{
                position: relative;
                top: 0;
                width: 100%;
                max-height: none;
                margin-bottom: 2rem;
            }}
        }}

        @media (max-width: 768px) {{
            .container {{
                padding: 1rem;
            }}

            .header {{
                flex-direction: column;
                gap: 1rem;
            }}

            h1 {{
                font-size: 1.75rem;
            }}

            h2 {{
                font-size: 1.5rem;
            }}

            h3 {{
                font-size: 1.25rem;
            }}

            pre {{
                font-size: 0.8125rem;
            }}

            table {{
                display: block;
                overflow-x: auto;
                white-space: nowrap;
            }}
        }}

        /* Print styles */
        @media print {{
            .header,
            .sidebar,
            .theme-toggle,
            .print-btn,
            .back-to-top {{
                display: none !important;
            }}

            body {{
                background: white;
                color: black;
                font-size: 12pt;
            }}

            .container {{
                max-width: 100%;
                padding: 0;
            }}

            .content {{
                width: 100%;
            }}

            h1, h2, h3, h4, h5, h6 {{
                color: black;
                page-break-after: avoid;
            }}

            pre, table {{
                page-break-inside: avoid;
            }}

            a {{
                color: black;
                text-decoration: underline;
            }}

            a[href^="http"]::after {{
                content: " (" attr(href) ")";
                font-size: 10pt;
                color: #666;
            }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <h1>{short_title}</h1>
        <div class="header-controls">
            <button class="theme-toggle" onclick="toggleTheme()">Toggle Theme</button>
            <button class="print-btn" onclick="window.print()">Print / PDF</button>
        </div>
    </header>

    <div class="container">
        <div class="main-content">
            <aside class="sidebar">
                <nav class="toc">
                    <div class="toc-title">Table of Contents</div>
                    {toc}
                </nav>
            </aside>

            <article class="content">
                {content}
            </article>
        </div>
    </div>

    <footer class="footer">
        <p>Generated from Markdown on {date}</p>
        <p>Collaboration Intelligence Hub - Technical Documentation</p>
    </footer>

    <button class="back-to-top" onclick="scrollToTop()">Back to Top</button>

    <script>
        // Theme toggle
        function toggleTheme() {{
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        }}

        // Load saved theme
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {{
            document.documentElement.setAttribute('data-theme', savedTheme);
        }}

        // Back to top button visibility
        window.addEventListener('scroll', function() {{
            const btn = document.querySelector('.back-to-top');
            if (window.scrollY > 500) {{
                btn.classList.add('visible');
            }} else {{
                btn.classList.remove('visible');
            }}
        }});

        // Scroll to top function
        function scrollToTop() {{
            window.scrollTo({{
                top: 0,
                behavior: 'smooth'
            }});
        }}

        // Highlight current section in TOC
        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                const id = entry.target.getAttribute('id');
                const tocLink = document.querySelector(`.toc a[href="#${{id}}"]`);
                if (tocLink) {{
                    if (entry.isIntersecting) {{
                        tocLink.style.color = 'var(--accent-primary)';
                        tocLink.style.fontWeight = '600';
                    }} else {{
                        tocLink.style.color = '';
                        tocLink.style.fontWeight = '';
                    }}
                }}
            }});
        }}, {{
            rootMargin: '-80px 0px -80% 0px'
        }});

        // Observe all headings
        document.querySelectorAll('h1[id], h2[id], h3[id]').forEach(heading => {{
            observer.observe(heading);
        }});
    </script>
</body>
</html>'''


def extract_title(md_content: str) -> tuple[str, str]:
    """Extract title from markdown content."""
    lines = md_content.strip().split('\n')
    for line in lines:
        if line.startswith('# '):
            full_title = line[2:].strip()
            # Short title for header (first part before newline or dash)
            short_title = full_title.split(' - ')[0] if ' - ' in full_title else full_title[:50]
            return full_title, short_title
    return "Technical Documentation", "Documentation"


def convert_markdown_to_html(md_content: str) -> tuple[str, str]:
    """Convert markdown content to HTML with TOC."""

    # Configure markdown extensions
    md = markdown.Markdown(
        extensions=[
            'tables',
            'fenced_code',
            'codehilite',
            'toc',
            'attr_list',
            'nl2br',
            'sane_lists',
        ],
        extension_configs={
            'codehilite': {
                'css_class': 'codehilite',
                'guess_lang': True,
                'linenums': False,
            },
            'toc': {
                'title': '',
                'toc_depth': 3,
                'permalink': False,
            },
        }
    )

    # Convert markdown to HTML
    html_content = md.convert(md_content)

    # Get TOC
    toc = md.toc

    return html_content, toc


def process_file(input_path: str, output_path: Optional[str] = None) -> str:
    """Process a markdown file and convert to HTML."""

    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Determine output path
    if output_path is None:
        output_path = input_path.with_suffix('.html')
    else:
        output_path = Path(output_path)

    # Read markdown content
    with open(input_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Extract title
    full_title, short_title = extract_title(md_content)

    # Convert to HTML
    html_content, toc = convert_markdown_to_html(md_content)

    # Get current date
    from datetime import datetime
    current_date = datetime.now().strftime("%B %d, %Y")

    # Generate full HTML
    full_html = HTML_TEMPLATE.format(
        title=full_title,
        short_title=short_title,
        toc=toc,
        content=html_content,
        date=current_date
    )

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_html)

    return str(output_path)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Convert Markdown to beautifully styled HTML',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python md_to_html.py                           # Convert TECHNICAL_ARCHITECTURE.md
  python md_to_html.py README.md                 # Convert README.md to README.html
  python md_to_html.py input.md output.html      # Specify both input and output
        '''
    )

    parser.add_argument(
        'input',
        nargs='?',
        default='TECHNICAL_ARCHITECTURE.md',
        help='Input markdown file (default: TECHNICAL_ARCHITECTURE.md)'
    )

    parser.add_argument(
        'output',
        nargs='?',
        default=None,
        help='Output HTML file (default: same name with .html extension)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    try:
        if args.verbose:
            print(f"Converting: {args.input}")

        output_file = process_file(args.input, args.output)

        print(f"Successfully converted to: {output_file}")

        # Print file size
        size = Path(output_file).stat().st_size
        if size > 1024 * 1024:
            print(f"Output size: {size / (1024 * 1024):.2f} MB")
        elif size > 1024:
            print(f"Output size: {size / 1024:.2f} KB")
        else:
            print(f"Output size: {size} bytes")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
