"""Builds the ApexIQ project report in the MIT-ADT college format.

The college template (template.docx, the department's report layout with its logos, margins, footer and page numbering) is
opened, its front pages are rewritten for ApexIQ, and every chapter is generated with the template's own paragraph formats.
Word exports the PDF; a second pass fills the page numbers of the contents, figures and tables lists from that PDF.

Usage: python college_report/build_report.py   (needs python-docx, pymupdf and Microsoft Word on macOS)
"""
import copy
import os
import re
import subprocess

import docx
import fitz  # pymupdf
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches

from content import BIB, CHAPTERS, FRONT

HERE = os.path.dirname(os.path.abspath(__file__))
DOCX, PDF = os.path.join(HERE, "ApexIQ_Project_Report.docx"), os.path.join(HERE, "ApexIQ_Project_Report.pdf")
TNR = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman" w:eastAsia="Times New Roman"/>'
ARIAL = '<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial" w:eastAsia="Arial"/>'


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def runs(text, size=24, bold=False, italic=False, font=TNR):
    """Text with **bold** spans as Word runs."""
    out = []
    for i, part in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        if part:
            b = bold or i % 2 == 1
            out.append(f'<w:r><w:rPr>{font}<w:b w:val="{int(b)}"/><w:i w:val="{int(italic)}"/><w:sz w:val="{size}"/></w:rPr>'
                       f'<w:t xml:space="preserve">{esc(part)}</w:t></w:r>')
    return "".join(out)


def para(ppr, body):
    return parse_xml(f"<w:p {nsdecls('w')}><w:pPr>{ppr}</w:pPr>{body}</w:p>")


BODY_PPR = '<w:spacing w:before="0" w:after="120" w:line="360" w:lineRule="auto"/><w:ind w:left="0" w:firstLine="432"/><w:jc w:val="both"/>'
TEXT_WIDTH = 11909 - 2 * 1440  # page width minus the template's equal 1-inch left and right margins (twips)
TOC_TAB = '<w:tabs><w:tab w:pos="8928" w:val="right" w:leader="dot"/></w:tabs>'


def breakable(text):
    """Lets long identifiers such as FACT_RACE_RESULTS wrap at underscores instead of stretching justified lines."""
    return re.sub(r"(?<=[A-Za-z0-9])_(?=[A-Za-z0-9])", "_\u200b", text)


def p_body(text):
    return para(BODY_PPR, runs(breakable(text)))


def p_heading(level, text):
    if level == 1:
        return para('<w:pStyle w:val="Heading1"/><w:keepNext/><w:pageBreakBefore/><w:spacing w:before="0" w:after="360" w:line="240" w:lineRule="auto"/>'
                    '<w:ind w:left="0" w:firstLine="0"/><w:jc w:val="center"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr>', runs(text, 36, True, font=ARIAL))
    space = '<w:spacing w:before="240" w:after="120" w:line="240" w:lineRule="auto"/>' if level == 2 else \
        '<w:spacing w:before="200" w:after="80" w:line="240" w:lineRule="auto"/>'
    return para(f'<w:pStyle w:val="Heading{level}"/><w:keepNext/>{space}<w:ind w:left="0" w:firstLine="0"/><w:jc w:val="both"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr>',
                runs(text, 24, True))


def p_front_title(text):
    return para('<w:pageBreakBefore/><w:spacing w:before="240" w:after="360" w:line="240" w:lineRule="auto"/><w:ind w:left="0"/><w:jc w:val="center"/>',
                runs(text, 32, True, font=ARIAL))


def p_bullet(text):
    return para('<w:spacing w:before="0" w:after="40" w:line="360" w:lineRule="auto"/><w:ind w:left="720" w:hanging="360"/><w:jc w:val="both"/>'
                '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="9001"/></w:numPr>', runs(breakable(text)))


def p_caption(text, table):
    style = "TableCaption" if table else "FigureCaption"
    space = '<w:spacing w:before="120" w:after="0" w:line="240" w:lineRule="auto"/>' if table else \
        '<w:spacing w:before="0" w:after="200" w:line="240" w:lineRule="auto"/>'
    return para(f'<w:pStyle w:val="{style}"/>{"<w:keepNext/>" if table else ""}{space}<w:ind w:left="0"/><w:jc w:val="center"/>', runs(text, 20, True))


def p_equation(text, number):
    return para('<w:tabs><w:tab w:pos="8640" w:val="right"/></w:tabs><w:spacing w:before="60" w:after="120" w:line="360" w:lineRule="auto"/>'
                '<w:ind w:left="720"/>', runs(text, italic=True) + f'<w:r><w:rPr>{TNR}<w:sz w:val="24"/></w:rPr><w:tab/><w:t>({number})</w:t></w:r>')


def p_toc(text, page, level=0, bold=False):
    return para(f'{TOC_TAB}<w:spacing w:before="0" w:after="0" w:line="360" w:lineRule="auto"/><w:ind w:left="{504 * level}"/><w:jc w:val="both"/>',
                f'<w:r><w:rPr>{TNR}<w:b w:val="{int(bold)}"/><w:sz w:val="24"/></w:rPr><w:t xml:space="preserve">{esc(text)}</w:t><w:tab/><w:t>{page}</w:t></w:r>')


def p_bib(n, text):
    return para('<w:spacing w:before="0" w:after="120" w:line="360" w:lineRule="auto"/><w:ind w:left="648" w:hanging="648"/><w:jc w:val="both"/>',
                f'<w:r><w:rPr>{TNR}<w:sz w:val="24"/></w:rPr><w:t>[{n}]</w:t><w:tab/><w:t xml:space="preserve">{esc(text)}</w:t></w:r>')


def p_gap():
    return para('<w:spacing w:before="0" w:after="120" w:line="240" w:lineRule="auto"/>', "")


def table(headers, rows, widths):
    total = sum(widths)
    widths = [round(TEXT_WIDTH * w / total) for w in widths]

    def cell(text, w, head):
        shade = '<w:shd w:val="clear" w:color="auto" w:fill="E3ECD6"/>' if head else ""
        return (f'<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="{w}"/>{shade}</w:tcPr><w:p><w:pPr><w:spacing w:before="20" w:after="20" w:line="240" w:lineRule="auto"/>'
                f'<w:ind w:firstLine="0" w:left="0"/><w:jc w:val="both"/></w:pPr>{runs(str(text), 20, head)}</w:p></w:tc>')
    xml = (f'<w:tbl {nsdecls("w")}><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:type="dxa" w:w="{TEXT_WIDTH}"/><w:jc w:val="center"/><w:tblInd w:w="0" w:type="dxa"/>'
           '<w:tblLook w:firstColumn="1" w:firstRow="1" w:lastColumn="0" w:lastRow="0" w:noHBand="0" w:noVBand="1" w:val="04A0"/>'
           '<w:tblLayout w:type="fixed"/></w:tblPr><w:tblGrid>' + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + "</w:tblGrid>"
           '<w:tr><w:trPr><w:tblHeader w:val="true"/><w:cantSplit/></w:trPr>' + "".join(cell(h, w, True) for h, w in zip(headers, widths)) + "</w:tr>"
           + "".join("<w:tr><w:trPr><w:cantSplit/></w:trPr>" + "".join(cell(c, w, False) for c, w in zip(r, widths)) + "</w:tr>" for r in rows)
           + "</w:tbl>")
    return parse_xml(xml)


def cropped(path, crop):
    """Screenshots are cut to the part a reader needs; every image is written to figures/crops as an RGB JPEG."""
    from PIL import Image
    img = Image.open(os.path.join(HERE, path))
    if img.mode != "RGB":  # flatten transparency onto white
        img = Image.alpha_composite(Image.new("RGBA", img.size, "white"), img.convert("RGBA")).convert("RGB")
    if crop:
        top, height = crop
        img = img.crop((0, top, img.width, min(img.height, top + height)))
    out = os.path.join(HERE, "figures", "crops", os.path.splitext(os.path.basename(path))[0] + ".jpg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out, "JPEG", quality=92)
    return out


# ------------------------------------------------------------------ numbering of tables, figures, equations and citations

def number_everything():
    """Pre-pass: Table/Figure/equation numbers per chapter and IEEE citation numbers by first appearance."""
    labels, cites, lof, lot = {}, {}, [], []
    for ch, (title, blocks) in enumerate(CHAPTERS, 1):
        counts = {"table": 0, "fig": 0, "eq": 0}
        for b in blocks:
            kind = b[0]
            if kind in counts:
                assert b[1] not in labels, f"duplicate label {b[1]}"
                counts[kind] += 1
                labels[b[1]] = f"{ch}.{counts[kind]}"
                if kind == "table":
                    lot.append((b[1], f"Table {ch}.{counts[kind]}: {b[2]}"))
                elif kind == "fig":
                    lof.append((b[1], f"Figure {ch}.{counts[kind]}: {b[3]}"))
            for t in texts_of(b):
                for group in re.findall(r"\[@([^\]]+)\]", t):
                    for k in [k.strip().lstrip("@") for k in group.split(",")]:
                        assert k in BIB, f"unknown reference {k}"
                        cites.setdefault(k, len(cites) + 1)
    assert set(cites) == set(BIB), f"references never cited: {set(BIB) - set(cites)}"
    return labels, cites, lof, lot


def texts_of(b):
    kind = b[0]
    if kind in ("p", "def"):
        return [b[-1]]
    if kind == "bullets":
        return b[1]
    if kind == "table":
        return [c for r in b[4] for c in r]
    return []


def resolve(text, labels, cites):
    text = re.sub(r"\{(?:tab|fig|eq):([\w-]+)\}", lambda m: labels[m.group(1)], text)
    return re.sub(r"\[@([^\]]+)\]", lambda m: "[" + ", ".join(str(cites[k.strip().lstrip("@")]) for k in m.group(1).split(",")) + "]", text)


# ------------------------------------------------------------------ front pages of the template

def set_text(p, old, new):
    """Replaces text inside the runs of a template paragraph, keeping their formatting."""
    hits = 0
    for r in p.runs:
        if old in r.text:
            r.text, hits = r.text.replace(old, new), hits + 1
    assert hits, f"'{old}' not found in: {p.text[:80]}"


def rewrite(p, xml_runs):
    for r in list(p._p):
        if r.tag != qn("w:pPr"):
            p._p.remove(r)
    for r in parse_xml(f"<w:p {nsdecls('w')}>{xml_runs}</w:p>"):
        p._p.append(r)


def front_pages(d, els):
    P = lambda i: docx.text.paragraph.Paragraph(els[i], d)
    T = lambda i: docx.table.Table(els[i], d)
    title_old = "DEBTSCOPE: PREDICTIVE ENGINEERING INTELLIGENCE FOR TECHNICAL DEBT PRIORITIZATION"
    rewrite(P(2), runs(FRONT["title"].upper(), 32, True, font=ARIAL))
    for tbl, keep in ((T(13), 2), (T(50), 3)):  # two team members
        for row in tbl.rows[keep:]:
            tbl._tbl.remove(row._tr)
    set_text(P(15), "Prof. Sushma Mehetre", FRONT["guide"])
    rewrite(P(30), runs(f"“{FRONT['title'].upper()}”", 24, True))
    for i in (34, 35, 58, 59, 96, 97):
        els[i].getparent().remove(els[i])
    set_text(P(36), "Prof. Sushma Mehetre", FRONT["guide"])
    set_text(T(39).cell(0, 0).paragraphs[0], "Prof. Sushma Mehetre", FRONT["guide"])
    for row in T(41).rows:  # signatures: Guide, Head of Department, Dean (no PBL coordinator)
        row._tr.remove(row.cells[0]._tc)
    grid = els[41].find(qn("w:tblGrid"))
    grid.remove(grid[0])
    set_text(P(52), "DebtScope: Predictive Engineering Intelligence for Technical Debt Prioritization", FRONT["title"])
    set_text(P(63), "Prof. Sushma Mehetre", FRONT["guide"])
    rewrite(P(78), runs(FRONT["examiner"]))
    rewrite(P(91), runs(FRONT["acknowledgement"]))
    assert title_old not in "".join(e.xpath("string(.)") for e in els[:98] if e.getparent() is not None)


# ------------------------------------------------------------------ build

def build(pages):
    d = docx.Document(os.path.join(HERE, "template.docx"))
    body = d.element.body
    els = list(body.iterchildren())
    front_end = els[229]  # paragraph holding the front matter's section break (roman page numbers)
    assert front_end.find(".//" + qn("w:sectPr")) is not None and "ABSTRACT" in els[98].xpath("string(.)")
    for e in els[98:229] + els[230:-1]:
        body.remove(e)
    front_pages(d, els)
    labels, cites, lof, lot = number_everything()
    pg = lambda key: pages.get(key, "0")

    front = [p_front_title("ABSTRACT")] + [p_body(resolve(t, labels, cites)) for t in FRONT["abstract"]]
    front += [p_front_title("CONTENTS")]
    for name, key in (("Certificate", "Certificate"), ("Declaration", "Declaration"), ("Examiner’s Approval Certificate", "Examiner"),
                      ("Acknowledgement", "Acknowledgement"), ("Abstract", "Abstract"), ("List of Figures", "LIST OF FIGURES"),
                      ("List of Tables", "LIST OF TABLES")):
        front.append(p_toc(name, pg(key)))
    front.append(p_gap())
    for title, blocks in CHAPTERS:
        front.append(p_toc(title, pg(title), 0, True))
        front += [p_toc(b[1], pg(b[1]), 1) for b in blocks if b[0] == "h2"]
    front.append(p_toc("BIBLIOGRAPHY", pg("BIBLIOGRAPHY"), 0, True))
    front += [p_front_title("LIST OF FIGURES")] + [p_toc(t, pg(k)) for k, t in lof]
    front += [p_front_title("LIST OF TABLES")] + [p_toc(t, pg(k)) for k, t in lot]
    for e in front:
        front_end.addprevious(e)

    def add(e):
        body.sectPr.addprevious(e)

    for ch, (title, blocks) in enumerate(CHAPTERS, 1):
        add(p_heading(1, title))
        for b in blocks:
            kind = b[0]
            if kind in ("h2", "h3"):
                add(p_heading(int(kind[1]), b[1]))
            elif kind == "p":
                add(p_body(resolve(b[1], labels, cites)))
            elif kind == "def":
                add(p_body(f"**{b[1]}:** " + resolve(b[2], labels, cites)))
            elif kind == "bullets":
                for t in b[1]:
                    add(p_bullet(resolve(t, labels, cites)))
            elif kind == "eq":
                add(p_equation(b[2], labels[b[1]]))
            elif kind == "table":  # ("table", key, caption, headers, rows, widths)
                add(p_caption(f"Table {labels[b[1]]}: {b[2]}", True))
                add(table(b[3], [[resolve(str(c), labels, cites) for c in r] for r in b[4]], b[5]))
                add(p_gap())
            elif kind == "fig":  # ("fig", key, image, caption, width_in[, (top_px, height_px) crop])
                p = d.add_paragraph()  # python-docx appends before the final section properties
                p._p.insert(0, parse_xml(f'<w:pPr {nsdecls("w")}><w:keepNext/><w:spacing w:before="120" w:after="60" w:line="240" w:lineRule="auto"/>'
                                         '<w:ind w:left="0"/><w:jc w:val="center"/></w:pPr>'))
                p.add_run().add_picture(cropped(b[2], b[5] if len(b) > 5 else None), width=Inches(b[4]))
                add(p_caption(f"Figure {labels[b[1]]}: {b[3]}", False))
            else:
                raise ValueError(kind)
    add(p_heading(1, "BIBLIOGRAPHY"))
    for k, n in sorted(cites.items(), key=lambda kv: kv[1]):
        add(p_bib(n, BIB[k]))
    used = set(re.findall(r'r:(?:embed|id)="([^"]+)"', body.xml))
    for rid, rel in list(d.part.rels.items()):
        if rel.reltype.endswith("/image") and rid not in used:
            d.part.rels.pop(rid)
    d.save(DOCX)
    return lof, lot


def export_pdf():
    """Apple Pages renders the .docx to PDF (Microsoft Word is not installed on this Mac)."""
    subprocess.run(["open", "-a", "Pages"], check=True)
    script = f'''tell application "Pages"
        set d to open POSIX file "{DOCX}"
        delay 10
        export d to POSIX file "{PDF}" as PDF
        close d saving no
    end tell'''
    subprocess.run(["osascript", "-e", script], check=True, capture_output=True, timeout=600)


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def page_numbers(lof, lot):
    """Reads the exported PDF: roman numbers for the front pages, arabic from Chapter 1 (which starts at 1)."""
    doc = fitz.open(PDF)
    text = [norm(p.get_text()) for p in doc]
    start = next(i for i, t in enumerate(text) if "MITSOC, Department" in t)
    roman = lambda n: ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii", "xiii", "xiv", "xv"][n - 1]
    pages = {}
    for key in ("CERTIFICATE", "DECLARATION", "EXAMINER’S APPROVAL", "ACKNOWLEDGEMENT", "ABSTRACT", "LIST OF FIGURES", "LIST OF TABLES"):
        i = next(i for i in range(1, start) if text[i].startswith(key) or f" {key}" in text[i][:200])
        pages[{"CERTIFICATE": "Certificate", "DECLARATION": "Declaration", "EXAMINER’S APPROVAL": "Examiner",
               "ACKNOWLEDGEMENT": "Acknowledgement", "ABSTRACT": "Abstract"}.get(key, key)] = roman(i)

    def find(needle):
        return str(next(i for i in range(start, len(text)) if norm(needle) in text[i]) - start + 1)
    for title, blocks in CHAPTERS:
        pages[title] = find(title)
        for b in blocks:
            if b[0] == "h2":
                pages[b[1]] = find(b[1])
    for key, cap in lof + lot:
        pages[key] = find(cap.split(":")[0] + ":")
    pages["BIBLIOGRAPHY"] = find("BIBLIOGRAPHY [1]")
    return pages, len(doc)


if __name__ == "__main__":
    lof, lot = build({})
    export_pdf()
    pages, n = page_numbers(lof, lot)
    build(pages)
    export_pdf()
    again, n = page_numbers(lof, lot)
    assert again == pages, "page numbers moved between passes"
    print(f"[+] {DOCX}\n[+] {PDF} ({n} pages, {len(lof)} figures, {len(lot)} tables)")
