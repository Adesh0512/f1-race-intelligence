import re
import html

def md_to_html(md_text):
    lines = md_text.split('\n')
    html_lines = []
    in_table = False
    table_rows = []
    in_code = False
    code_lines = []

    def flush_table():
        nonlocal in_table, table_rows, html_lines
        if not table_rows:
            in_table = False
            return
        res = ['<div class="table-container"><table>']
        header = table_rows[0]
        res.append('<thead><tr>')
        for c in header:
            res.append(f'<th>{c.strip()}</th>')
        res.append('</tr></thead><tbody>')
        for r in table_rows[1:]:
            res.append('<tr>')
            for c in r:
                res.append(f'<td>{c.strip()}</td>')
            res.append('</tr>')
        res.append('</tbody></table></div>')
        html_lines.append('\n'.join(res))
        table_rows = []
        in_table = False

    def format_inline(text):
        # bold
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # italic
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        # code
        text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
        return text

    for line in lines:
        stripped = line.strip()

        # Handle page breaks
        if '<div style="page-break-after: always;"></div>' in line:
            if in_table:
                flush_table()
            html_lines.append('<div class="page-break"></div>')
            continue

        # Handle code blocks
        if stripped.startswith('```'):
            if in_code:
                in_code = False
                code_content = html.escape('\n'.join(code_lines))
                html_lines.append(f'<pre><code>{code_content}</code></pre>')
                code_lines = []
            else:
                if in_table:
                    flush_table()
                in_code = True
                code_lines = []
            continue

        if in_code:
            code_lines.append(line)
            continue

        # Handle tables
        if stripped.startswith('|') and stripped.endswith('|'):
            # Table separator line
            if re.match(r'^\|[\s\-:]+(\|[\s\-:]+)+\|$', stripped):
                continue
            cells = [format_inline(c) for c in stripped.strip('|').split('|')]
            if not in_table:
                in_table = True
                table_rows = [cells]
            else:
                table_rows.append(cells)
            continue
        else:
            if in_table:
                flush_table()

        if not stripped:
            html_lines.append('')
            continue

        # Headings
        if stripped.startswith('# '):
            title = format_inline(stripped[2:])
            html_lines.append(f'<h1 class="chapter-title">{title}</h1>')
        elif stripped.startswith('## '):
            title = format_inline(stripped[3:])
            html_lines.append(f'<h2 class="section-title">{title}</h2>')
        elif stripped.startswith('### '):
            title = format_inline(stripped[4:])
            html_lines.append(f'<h3 class="subsection-title">{title}</h3>')
        elif stripped.startswith('#### '):
            title = format_inline(stripped[5:])
            html_lines.append(f'<h4 class="subsubsection-title">{title}</h4>')
        elif stripped.startswith('* ') or stripped.startswith('- ') or stripped.startswith('• '):
            bullet = format_inline(stripped[2:])
            html_lines.append(f'<p class="bullet-item">• {bullet}</p>')
        elif re.match(r'^\d+\.\s', stripped):
            item = format_inline(re.sub(r'^\d+\.\s', '', stripped))
            num = re.match(r'^\d+\.', stripped).group(0)
            html_lines.append(f'<p class="numbered-item"><b>{num}</b> {item}</p>')
        elif stripped.startswith('---'):
            html_lines.append('<hr class="divider">')
        elif stripped.startswith('> '):
            quote = format_inline(stripped[2:])
            html_lines.append(f'<blockquote class="callout">{quote}</blockquote>')
        else:
            p = format_inline(stripped)
            html_lines.append(f'<p class="para">{p}</p>')

    if in_table:
        flush_table()

    body = '\n'.join(html_lines)
    return body

with open('PROJECT_REPORT_DWDM_APEXIQ.md', 'r', encoding='utf-8') as f:
    md_content = f.read()

body_html = md_to_html(md_content)

html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>ApexIQ Project Report</title>
<style>
  @page {{
    size: A4 portrait;
    margin: 25.4mm 25.4mm 25.4mm 31.75mm; /* Top 1", Bottom 1", Right 1", Left 1.25" */
    @bottom-center {{
      content: "MITSOC, Department of Computer Engineering, 2025-26";
      font-family: "Times New Roman", Times, serif;
      font-size: 10pt;
      color: #333333;
    }}
  }}
  body {{
    font-family: "Times New Roman", Times, serif;
    font-size: 12pt;
    line-height: 1.5;
    color: #111111;
    margin: 0;
    padding: 0;
    text-align: justify;
    background: #FFFFFF;
  }}
  .chapter-title {{
    font-size: 18pt;
    font-weight: bold;
    text-align: center;
    text-transform: uppercase;
    margin-top: 24pt;
    margin-bottom: 14pt;
    color: #000000;
  }}
  .section-title {{
    font-size: 13pt;
    font-weight: bold;
    text-transform: uppercase;
    margin-top: 18pt;
    margin-bottom: 8pt;
    color: #000000;
  }}
  .subsection-title {{
    font-size: 12pt;
    font-weight: bold;
    margin-top: 14pt;
    margin-bottom: 6pt;
    color: #111111;
  }}
  .subsubsection-title {{
    font-size: 11pt;
    font-weight: bold;
    font-style: italic;
    margin-top: 10pt;
    margin-bottom: 4pt;
    color: #222222;
  }}
  .para {{
    margin-bottom: 8pt;
    text-indent: 1.5em;
  }}
  .bullet-item {{
    margin-left: 2em;
    margin-bottom: 4pt;
    text-indent: -1em;
  }}
  .numbered-item {{
    margin-left: 2em;
    margin-bottom: 4pt;
    text-indent: -1.2em;
  }}
  .table-container {{
    margin: 14pt 0;
    width: 100%;
    overflow-x: auto;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 8pt 0;
    font-size: 10.5pt;
  }}
  th, td {{
    border: 1px solid #333333;
    padding: 6pt 8pt;
    text-align: left;
    vertical-align: top;
  }}
  th {{
    background-color: #F0F2F5;
    font-weight: bold;
  }}
  tr:nth-child(even) td {{
    background-color: #FAFAFA;
  }}
  pre {{
    background: #F4F6F8;
    border: 1px solid #D0D7DE;
    padding: 10pt;
    font-family: "Courier New", Courier, monospace;
    font-size: 9.5pt;
    border-radius: 4px;
    overflow-x: auto;
    margin: 12pt 0;
    line-height: 1.3;
  }}
  code {{
    font-family: "Courier New", Courier, monospace;
    font-size: 10.5pt;
    background: #F0F2F5;
    padding: 1pt 3pt;
    border-radius: 3px;
  }}
  .divider {{
    border: none;
    border-top: 1px solid #CCCCCC;
    margin: 18pt 0;
  }}
  .page-break {{
    page-break-after: always;
    break-after: page;
    height: 0;
    display: block;
  }}
  .footer-text {{
    text-align: center;
    font-size: 10pt;
    color: #555555;
    margin-top: 20pt;
    border-top: 1px solid #E0E0E0;
    padding-top: 6pt;
  }}
  @media print {{
    .page-break {{
      page-break-after: always;
      break-after: page;
    }}
  }}
</style>
</head>
<body>
{body_html}
</body>
</html>
"""

with open('PROJECT_REPORT_DWDM_APEXIQ.html', 'w', encoding='utf-8') as f:
    f.write(html_template)

print("Successfully converted PROJECT_REPORT_DWDM_APEXIQ.md to PROJECT_REPORT_DWDM_APEXIQ.html")
