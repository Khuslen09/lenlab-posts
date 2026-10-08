#!/usr/bin/env python3
"""LENLAB Instagram post renderer (FIXED template: every element has a fixed position and size;
overflowing text makes the script exit 1 instead of shrinking). Usage: python3 render_post.py posts.json OUT_DIR
posts.json = [{"slug","category","date","en","ko","mn","stat","stat_label","entities":[..],"theme":"light"|"dark"}]"""
import asyncio, json, sys, html, os
from playwright.async_api import async_playwright

RED, INK, PAPER = "#D0271D", "#111111", "#FFFFFF"

def logo(size, dark=False):
    fill, txt, line = ("#111111", "#F5F2EE", "#AA221A") if dark else ("#F5F2EE", "#111111", "#D84F47")
    return (f'<svg viewBox="0 0 512 512" width="{size}" height="{size}">'
            f'<circle cx="256" cy="256" r="245.5" fill="none" stroke="#D0261C" stroke-opacity="0.4" stroke-width="2.5"/>'
            f'<circle cx="256" cy="256" r="230" fill="{fill}"/>'
            f'<text x="256" y="294" text-anchor="middle" font-family="DejaVu Serif" font-weight="bold" font-size="132" fill="{txt}">LEN</text>'
            f'<line x1="100" y1="320.5" x2="412" y2="320.5" stroke="{line}" stroke-width="2.5"/>'
            f'<text x="264" y="384" text-anchor="middle" font-family="DejaVu Serif" font-size="35" letter-spacing="16" fill="#D0271D">lab</text></svg>')

CSS = f"""
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;background:{PAPER};color:{INK};font-family:'DejaVu Serif','Noto Serif CJK KR',serif;position:relative;overflow:hidden}}
.abs{{position:absolute;left:80px;width:920px}}
.top{{top:72px;height:30px;display:flex;justify-content:space-between;align-items:center;font-family:'DejaVu Sans','Noto Sans CJK KR',sans-serif;
  font-size:22px;letter-spacing:4px;text-transform:uppercase;white-space:nowrap}}
.cat{{color:{RED};font-weight:bold;display:flex;align-items:center;gap:14px}}
.cat:before{{content:'';width:14px;height:14px;background:{RED};display:inline-block}}
.rule{{top:126px;height:3px;background:{INK}}}
.lang{{font-family:'DejaVu Sans',sans-serif;font-size:18px;letter-spacing:4px;color:{RED};font-weight:bold;height:22px}}
.l-en{{top:172px}} .l-ko{{top:404px}} .l-mn{{top:588px}}
.slot{{overflow:hidden}}
.en{{top:198px;height:176px;font-weight:bold;font-size:76px;line-height:1.14;letter-spacing:-0.5px}}
.ko{{top:430px;height:132px;font-family:'Noto Serif CJK KR',serif;font-weight:bold;font-size:50px;line-height:1.3;word-break:keep-all}}
.mn{{top:614px;height:100px;font-size:38px;line-height:1.3;color:#333}}
.statrule{{top:756px;height:1.5px;background:{INK}}}
.stat{{top:786px;height:118px;font-size:96px;line-height:1.15;color:{RED};font-weight:bold;letter-spacing:-1px;white-space:nowrap}}
.statl{{top:914px;height:80px;font-family:'Noto Sans CJK KR',sans-serif;font-size:26px;line-height:1.45;color:#333;white-space:pre-line}}
.footrule{{top:1110px;height:3px;background:{INK}}}
.foot{{top:1134px;height:150px;display:flex;justify-content:space-between;align-items:center}}
.ents{{display:flex;flex-wrap:nowrap;gap:12px;max-width:740px;overflow:hidden}}
.ent{{border:2px solid {INK};padding:9px 18px;font-family:'DejaVu Sans',sans-serif;font-weight:bold;font-size:20px;letter-spacing:3px;text-transform:uppercase;white-space:nowrap}}
.brand{{display:flex;align-items:center}}
"""

DARK = """
body{background:#111111;color:#F5F2EE}
.rule,.footrule,.statrule{background:#F5F2EE}
.mn{color:#CFCAC4}.statl{color:#BDB8B2}
.ent{border-color:#F5F2EE;color:#F5F2EE}
.cat,.lang,.stat{color:#E2372B}.cat:before{background:#E2372B}
"""

def page(p):
    e = lambda s: html.escape(s or "")
    dark = p.get("theme") == "dark"
    ents = "".join(f'<div class="ent">{e(x)}</div>' for x in p.get("entities", [])[:3])
    stat = (f'<div class="abs slot stat">{e(p["stat"])}</div><div class="abs slot statl">{e(p.get("stat_label"))}</div>'
            if p.get("stat") else '')
    return f"""<html><head><meta charset="utf-8"><style>{CSS}{DARK if dark else ""}</style></head><body>
<div class="abs top"><div class="cat">{e(p['category'])}</div><div>{e(p['date'])}</div></div>
<div class="abs rule"></div>
<div class="abs lang l-en">EN</div><div class="abs slot en">{e(p['en'])}</div>
<div class="abs lang l-ko">KO</div><div class="abs slot ko">{e(p['ko'])}</div>
<div class="abs lang l-mn">MN</div><div class="abs slot mn">{e(p['mn'])}</div>
<div class="abs statrule"></div>
{stat}
<div class="abs footrule"></div>
<div class="abs foot"><div class="ents">{ents}</div><div class="brand">{logo(150)}</div></div>
</body></html>"""

CHECK = """() => { const bad=[];
 for (const [sel,name] of [['.en','en (max 2 lines)'],['.ko','ko (max 2 lines)'],['.mn','mn (max 2 lines)'],['.statl','stat_label (max 2 lines)']]) {
   const el=document.querySelector(sel); if (el && el.scrollHeight > el.clientHeight+1) bad.push(name); }
 const st=document.querySelector('.stat'); if (st && st.scrollWidth > st.clientWidth+1) bad.push('stat (too wide, one line)');
 const en=document.querySelector('.ents'); if (en && en.scrollWidth > en.clientWidth+1) bad.push('entities (too long, one row)');
 const top=document.querySelector('.top'); if (top && top.scrollWidth > top.clientWidth+1) bad.push('category/date (too long)');
 return bad; }"""

async def main(src, out):
    posts = json.load(open(src, encoding="utf-8"))
    os.makedirs(out, exist_ok=True)
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        errors = []
        for p in posts:
            await pg.set_content(page(p)); await pg.wait_for_timeout(200)
            bad = await pg.evaluate(CHECK)
            if bad:
                errors.append(f"{p['slug']}: TEXT TOO LONG -> shorten: " + ", ".join(bad))
            path = os.path.join(out, f"{p['slug']}.png")
            await pg.screenshot(path=path); print(path)
        await b.close()
    if errors:
        print("\n".join(errors), file=sys.stderr)
        print("FIXED TEMPLATE: font sizes never change. Shorten the listed fields and re-run.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2]))
