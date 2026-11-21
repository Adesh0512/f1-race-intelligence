"""
Regenerates the Mermaid ER diagrams from the warehouse DDL, so the diagrams always
match create_star_schema.sql / create_snowflake_schema.sql (and f1_warehouse.db).
Usage: python3 00_data_warehouse/generate_er_diagrams.py
"""

import os
import re
import sqlite3

DW = os.path.dirname(os.path.abspath(__file__))


def ddl_to_mermaid(ddl_file):
    c = sqlite3.connect(":memory:")
    c.executescript(open(os.path.join(DW, ddl_file), encoding="utf-8").read())
    tables = [t for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    lines = ["erDiagram"]
    rels = []
    for t in tables:
        fks = {fk[3]: fk[2] for fk in c.execute(f'PRAGMA foreign_key_list("{t}")')}
        lines.append(f"    {t} {{")
        for _, col, typ, _, _, pk in c.execute(f'PRAGMA table_info("{t}")'):
            typ = re.sub(r"[^A-Za-z0-9_]", "", typ.split("(")[0]) or "TEXT"  # Mermaid types cannot contain ( or ,
            key = "PK" if pk else ("FK" if col in fks else "")
            lines.append(f"        {typ} {col} {key}".rstrip())
        lines.append("    }")
        rels += [f'    {parent} ||--o{{ {t} : "{col}"' for col, parent in fks.items()]
    return "\n".join(lines + [""] + rels) + "\n"


if __name__ == "__main__":
    for ddl, out in [("create_star_schema.sql", "er_diagram_star.mmd"), ("create_snowflake_schema.sql", "er_diagram_snowflake.mmd")]:
        text = ddl_to_mermaid(ddl)
        assert text.startswith("erDiagram") and "||--o{" in text
        open(os.path.join(DW, out), "w", encoding="utf-8").write(text)
        print(f"[+] {out}: {text.count(' {')} entities, {text.count('||--o{')} relationships")
