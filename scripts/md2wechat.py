#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 Markdown 转成微信公众号可粘贴的 HTML（内联样式、无禁用标签）。

用法：
    python3 md2wechat.py article.md --out output.html [--theme ink]

设计约束（来自公众号编辑器的实际限制）：
  - 禁用 h1/div/script/style/iframe/pre/code
  - 代码块用 section + 显式 <br>，否则多行会折叠成一行
  - 所有样式内联；不依赖外部 CSS
"""
import argparse
import html
import re
from pathlib import Path

THEMES = {
    "ink": {"accent": "#1f3a5f", "muted": "#6b6b76", "code_bg": "#f4f4f6"},
    "warm": {"accent": "#8a4b2a", "muted": "#6f625c", "code_bg": "#f8f1ea"},
}


def inline(text, t):
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`",
                  rf'<span style="background:{t["code_bg"]};padding:2px 5px;border-radius:4px;'
                  r'font-family:Menlo,Consolas,monospace;font-size:13px">\1</span>', text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1", text)  # 公众号不保留外链
    return text


def convert(md, t):
    out = []
    lines = md.splitlines()
    i = 0
    para = []

    def flush():
        if para:
            out.append(f'<p style="margin:0 0 18px;font-size:15px;line-height:1.85;color:#222">'
                       + inline(" ".join(para), t) + "</p>")
            para.clear()

    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith("```"):
            flush()
            i += 1
            code = []
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            body = "<br>".join(html.escape(c) or "&nbsp;" for c in code)
            out.append(
                f'<section style="background:{t["code_bg"]};border-radius:8px;padding:14px 16px;'
                f'margin:0 0 18px;font-family:Menlo,Consolas,monospace;font-size:13px;'
                f'line-height:1.7;color:#333;overflow-x:auto">{body}</section>')
            i += 1
            continue
        if line.startswith("# "):
            flush()
            out.append(f'<p style="margin:0 0 20px;font-size:22px;line-height:1.4;'
                       f'font-weight:700;color:{t["accent"]}">{inline(line[2:], t)}</p>')
        elif line.startswith("## "):
            flush()
            out.append(f'<section style="margin:28px 0 12px;padding-left:10px;'
                       f'border-left:4px solid {t["accent"]}">'
                       f'<p style="margin:0;font-size:18px;font-weight:700;color:{t["accent"]};'
                       f'line-height:1.5">{inline(line[3:], t)}</p></section>')
        elif line.startswith("> "):
            flush()
            quote = []
            while i < len(lines) and lines[i].rstrip().startswith("> "):
                quote.append(lines[i].rstrip()[2:])
                i += 1
            body = "<br>".join(inline(q, t) for q in quote)
            out.append(f'<section style="margin:0 0 18px;padding:12px 16px;'
                       f'background:{t["code_bg"]};border-left:3px solid {t["accent"]};'
                       f'border-radius:0 8px 8px 0">'
                       f'<p style="margin:0;font-size:15px;line-height:1.8;color:#444">'
                       f'{body}</p></section>')
            continue
        elif re.match(r"^[-*] ", line):
            flush()
            items = []
            while i < len(lines) and re.match(r"^[-*] ", lines[i].rstrip()):
                items.append(lines[i].rstrip()[2:])
                i += 1
            out.append('<ul style="margin:0 0 18px;padding-left:22px;font-size:15px;line-height:1.85;color:#222">'
                       + "".join(f"<li style='margin:6px 0'>{inline(x, t)}</li>" for x in items) + "</ul>")
            continue
        elif re.match(r"^\d+\. ", line):
            flush()
            items = []
            while i < len(lines) and re.match(r"^\d+\. ", lines[i].rstrip()):
                items.append(re.sub(r"^\d+\. ", "", lines[i].rstrip()))
                i += 1
            out.append('<ol style="margin:0 0 18px;padding-left:22px;font-size:15px;line-height:1.85;color:#222">'
                       + "".join(f"<li style='margin:6px 0'>{inline(x, t)}</li>" for x in items) + "</ol>")
            continue
        elif line.strip() in ("", "---"):
            flush()
        else:
            para.append(line.strip())
        i += 1
    flush()
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--out", required=True)
    ap.add_argument("--theme", default="ink", choices=THEMES)
    a = ap.parse_args()
    md = Path(a.src).read_text(encoding="utf-8")
    body = convert(md, THEMES[a.theme])
    doc = f"""<!doctype html><html lang="zh"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(Path(a.src).stem)}</title>
<body style="margin:0;background:#fff">
<section style="max-width:680px;margin:0 auto;padding:24px 18px;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Noto Sans SC',sans-serif">
{body}
</section></body></html>"""
    Path(a.out).write_text(doc, encoding="utf-8")
    print(f"html → {a.out}  ({len(doc)} B, {doc.count('<p ')} 段, {doc.count('<li ')} 列表项)")


if __name__ == "__main__":
    main()
