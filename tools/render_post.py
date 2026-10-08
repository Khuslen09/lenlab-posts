#!/usr/bin/env python3
"""LENLAB Instagram post renderer. Usage: python3 render_post.py posts.json OUT_DIR
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
body{{width:1080px;height:1350px;background:{PAPER};color:{INK};font-family:'DejaVu Serif','Noto Serif CJK KR',serif}}
.wrap{{position:absolute;inset:72px 80px 64px 80px;display:flex;flex-direction:column}}
.top{{display:flex;justify-content:space-between;align-items:center;font-family:'DejaVu Sans','Noto Sans CJK KR',sans-serif;
  font-size:22px;letter-spacing:4px;text-transform:uppercase}}
.cat{{color:{RED};font-weight:bold;display:flex;align-items:center;gap:14px}}
.cat:before{{content:'';width:14px;height:14px;background:{RED};display:inline-block}}
.rule{{height:3px;background:{INK};margin:28px 0 56px}}
.lang{{font-family:'DejaVu Sans',sans-serif;font-size:18px;letter-spacing:4px;color:{RED};font-weight:bold;margin-bottom:12px}}
.en{{font-weight:bold;font-size:82px;line-height:1.12;letter-spacing:-0.5px}}
.ko{{font-family:'Noto Serif CJK KR',serif;font-weight:bold;font-size:54px;line-height:1.3;word-break:keep-all}}
.mn{{font-size:42px;line-height:1.3;color:#333}}
.blk{{margin-bottom:44px}}
.stat{{margin-top:auto;border-top:1.5px solid {INK};padding-top:30px;display:flex;flex-direction:column;gap:10px}}
.stat b{{font-size:96px;color:{RED};font-weight:bold;letter-spacing:-1px;white-space:nowrap}}
.stat span{{font-family:'Noto Sans CJK KR',sans-serif;font-size:26px;line-height:1.45;color:#333;white-space:pre-line}}
.foot{{display:flex;justify-content:space-between;align-items:center;margin-top:36px;padding-top:28px;border-top:3px solid {INK}}}
.ents{{display:flex;flex-wrap:wrap;gap:12px;max-width:760px}}
.ent{{border:2px solid {INK};padding:9px 18px;font-family:'DejaVu Sans',sans-serif;font-weight:bold;font-size:20px;letter-spacing:3px;text-transform:uppercase}}
.brand{{display:flex;align-items:center;gap:16px;font-family:'DejaVu Sans',sans-serif;font-size:18px;letter-spacing:4px}}
"""

DARK = """
body{background:#111111;color:#F5F2EE}
.rule,.foot{background:none}.rule{background:#F5F2EE}
.foot{border-top-color:#F5F2EE}.stat{border-top-color:#F5F2EE}
.mn{color:#CFCAC4}.stat span{color:#BDB8B2}
.ent{border-color:#F5F2EE;color:#F5F2EE}
.cat,.lang,.stat b{color:#E2372B}.cat:before{background:#E2372B}
"""

def page(p):
    e = lambda s: html.escape(s or "")
    dark = p.get("theme") == "dark"
    ents = "".join(f'<div class="ent">{e(x)}</div>' for x in p.get("entities", [])[:3])
    stat = (f'<div class="stat"><b>{e(p["stat"])}</b><span>{e(p.get("stat_label"))}</span></div>'
            if p.get("stat") else '<div style="margin-top:auto"></div>')
    return f"""<html><head><meta charset="utf-8"><style>{CSS}{DARK if dark else ""}</style></head><body><div class="wrap">
<div class="top"><div class="cat">{e(p['category'])}</div><div>{e(p['date'])}</div></div>
<div class="rule"></div>
<div class="blk"><div class="lang">EN</div><div class="en">{e(p['en'])}</div></div>
<div class="blk"><div class="lang">KO</div><div class="ko">{e(p['ko'])}</div></div>
<div class="blk"><div class="lang">MN</div><div class="mn">{e(p['mn'])}</div></div>
{stat}
<div class="foot"><div class="ents">{ents}</div><div class="brand">{logo(150, not dark)}</div></div>
</div></body></html>"""

async def main(src, out):
    posts = json.load(open(src, encoding="utf-8"))
    os.makedirs(out, exist_ok=True)
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        for p in posts:
            await pg.set_content(page(p)); await pg.wait_for_timeout(200)
            # shrink EN title if it overflows the canvas
            for _ in range(8):
                over = await pg.evaluate("document.querySelector('.foot').getBoundingClientRect().bottom > 1295")
                if not over: break
                await pg.evaluate("for (const s of ['.en','.ko','.mn']){const el=document.querySelector(s);el.style.fontSize=(parseFloat(getComputedStyle(el).fontSize)*0.92)+'px'}")
            path = os.path.join(out, f"{p['slug']}.png")
            await pg.screenshot(path=path); print(path)
        await b.close()

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2]))
