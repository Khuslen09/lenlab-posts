#!/usr/bin/env python3
"""LENLAB Reels renderer: kinetic-typography vertical video (1080x1920, 30fps, ~20s), no voice.
Uses the same posts.json as render_post.py (needs what/why/summary). Output: <slug>-reel.mp4
Usage: python3 render_reel.py posts.json OUT_DIR [--only slug]
Music is added later in the Instagram app (licensed + better reach); the file has a silent audio track."""
import asyncio, json, sys, os, html, shutil, subprocess, tempfile
from playwright.async_api import async_playwright

W, H, FPS, DUR = 1080, 1920, 30, 20.0
RED_L, RED_D = "#D0271D", "#E2372B"

def logo(size, dark=False):
    fill, txt, line = ("#111111", "#F5F2EE", "#AA221A") if dark else ("#F5F2EE", "#111111", "#D84F47")
    return (f'<svg viewBox="0 0 512 512" width="{size}" height="{size}">'
            f'<circle cx="256" cy="256" r="245.5" fill="none" stroke="#D0261C" stroke-opacity="0.4" stroke-width="2.5"/>'
            f'<circle cx="256" cy="256" r="230" fill="{fill}"/>'
            f'<text x="256" y="294" text-anchor="middle" font-family="DejaVu Serif" font-weight="bold" font-size="132" fill="{txt}">LEN</text>'
            f'<line x1="100" y1="320.5" x2="412" y2="320.5" stroke="{line}" stroke-width="2.5"/>'
            f'<text x="264" y="384" text-anchor="middle" font-family="DejaVu Serif" font-size="35" letter-spacing="16" fill="#D0271D">lab</text></svg>')

def words(s, cls):
    return " ".join(f'<span class="w {cls}">{html.escape(x)}</span>' for x in (s or "").split())

def page(p):
    dark = p.get("theme") == "dark"
    bg, ink, sub, red = ("#111111", "#F5F2EE", "#BDB8B2", RED_D) if dark else ("#FFFFFF", "#111111", "#555555", RED_L)
    card = "#1B1B1B" if dark else "#FBFAF8"
    shadow = ("18px 22px 44px rgba(0,0,0,.65), -8px -8px 22px rgba(255,255,255,.045), inset 3px 3px 8px rgba(255,255,255,.06), inset -6px -6px 14px rgba(0,0,0,.45)"
              if dark else "18px 22px 44px rgba(17,17,17,.13), -10px -10px 26px rgba(255,255,255,.95), inset 6px 6px 12px rgba(255,255,255,.9), inset -8px -8px 16px rgba(17,17,17,.05)")
    e = lambda s: html.escape(s or "")
    secs = [("what", "What happened", "무슨 일?"), ("why", "Why it matters", "왜 중요할까?")]
    sec_html = ""
    for i, (k, t, kt) in enumerate(secs):
        d = p[k]
        sec_html += f"""<div class="scene" id="s{i+2}">
  <div class="sech"><span class="redbar"></span>{t}<span class="kt">{kt}</span></div>
  <div class="card body">
    <div class="ko">{words(d['ko'], 'k')}</div>
    <div class="en fade">{e(d['en'])}</div>
    <div class="mn fade2">{e(d['mn'])}</div>
  </div></div>"""
    s = p["summary"]
    return f"""<html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{H}px;background:{bg};color:{ink};overflow:hidden;position:relative;font-family:'DejaVu Serif','Noto Serif CJK KR',serif}}
.prog{{position:absolute;top:150px;left:80px;right:80px;display:flex;gap:10px}}
.prog i{{flex:1;height:5px;border-radius:3px;background:{ink}22;overflow:hidden}}
.prog i b{{display:block;height:100%;width:0;background:{red}}}
.topbar{{position:absolute;top:186px;left:80px;right:80px;display:flex;justify-content:space-between;font-family:'DejaVu Sans',sans-serif;
  font-size:26px;letter-spacing:5px;text-transform:uppercase;font-weight:bold}}
.cat{{color:{red}}} .date{{color:{sub};font-weight:normal}}
.scene{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;opacity:0}}
.w{{display:inline-block;opacity:0;transform:translateY(24px)}}
.t-en{{position:absolute;top:300px;left:80px;width:920px;font-weight:bold;font-size:76px;line-height:1.14;letter-spacing:-0.5px}}
.t-ko{{position:absolute;top:520px;left:80px;width:920px;font-family:'Noto Serif CJK KR',serif;font-weight:bold;font-size:60px;line-height:1.35;word-break:keep-all}}
.t-mn{{position:absolute;top:720px;left:80px;width:920px;font-size:40px;line-height:1.35;color:{sub}}}
.card{{position:absolute;left:52px;width:976px;border-radius:44px;background:{card};box-shadow:{shadow}}}
.statc{{top:960px;height:330px;padding:44px 28px}}
.stat{{font-weight:bold;font-size:120px;color:{red};letter-spacing:-2px;white-space:nowrap}}
.statl{{margin-top:14px;font-family:'Noto Sans CJK KR',sans-serif;font-size:32px;line-height:1.45;color:{sub};white-space:pre-line}}
.sech{{position:absolute;top:300px;left:80px;font-weight:bold;font-size:72px;display:flex;align-items:baseline;gap:22px}}
.redbar{{display:inline-block;width:14px;height:56px;background:{red};align-self:center}}
.kt{{font-family:'Noto Sans CJK KR',sans-serif;font-size:36px;color:{sub};font-weight:500}}
.body{{top:440px;min-height:900px;padding:60px 28px}}
.body .ko{{font-family:'Noto Sans CJK KR',sans-serif;font-weight:700;font-size:58px;line-height:1.5;word-break:keep-all}}
.body .en{{margin-top:44px;font-family:'DejaVu Sans',sans-serif;font-size:34px;line-height:1.5;color:{sub}}}
.body .mn{{margin-top:26px;font-family:'DejaVu Sans',sans-serif;font-size:31px;line-height:1.5;color:{sub}}}
.sum{{top:440px;min-height:760px;padding:70px 28px}}
.sum .ko{{font-family:'Noto Serif CJK KR',serif;font-weight:bold;font-size:76px;line-height:1.4;word-break:keep-all}}
.sum .en{{margin-top:50px;font-weight:bold;font-size:40px;line-height:1.4}}
.sum .mn{{margin-top:26px;font-size:34px;line-height:1.45;color:{sub}}}
.cta{{position:absolute;top:1300px;left:80px;width:920px;text-align:center;font-family:'DejaVu Sans',sans-serif;font-weight:bold;
  font-size:30px;letter-spacing:6px;color:{red};opacity:0}}
.handle{{position:absolute;top:1360px;left:80px;width:920px;text-align:center;font-family:'DejaVu Sans',sans-serif;font-size:30px;letter-spacing:3px;opacity:0}}
.brand{{position:absolute;top:1440px;left:470px;opacity:0}}
.fade,.fade2{{opacity:0}}
</style></head><body>
<div class="prog"><i><b></b></i><i><b></b></i><i><b></b></i><i><b></b></i></div>
<div class="topbar"><span class="cat">{e(p['category'])}</span><span class="date">{e(p['date'])}</span></div>
<div class="scene" id="s1">
  <div class="t-en">{words(p['en'], 'h').replace('-', chr(0x2011))}</div>
  <div class="t-ko fade">{e(p['ko'])}</div>
  <div class="t-mn fade2">{e(p['mn'])}</div>
  <div class="card statc pop"><div class="stat">{e(p['stat'])}</div><div class="statl">{e(p['stat_label'])}</div></div>
</div>
{sec_html}
<div class="scene" id="s4">
  <div class="sech"><span class="redbar"></span>In one line<span class="kt">한 줄 요약</span></div>
  <div class="card sum">
    <div class="ko">{words(s['ko'], 'k')}</div>
    <div class="en fade">{e(s['en'])}</div>
    <div class="mn fade2">{e(s['mn'])}</div>
  </div>
  <div class="cta">SAVE · SHARE · FOLLOW</div>
  <div class="handle">@lenlab.official</div>
  <div class="brand">{logo(140, not dark)}</div>
</div>
<script>
const SC=[[0,4.6],[4.6,9.8],[9.8,15.0],[15.0,{DUR}]];
const cl=x=>Math.max(0,Math.min(1,x)), ease=x=>1-Math.pow(1-cl(x),3);
function seq(els,t0,t1,t){{const n=els.length; els.forEach((el,i)=>{{const a=t0+(t1-t0)*i/Math.max(1,n);const k=ease((t-a)/0.35);
  el.style.opacity=k; el.style.transform=`translateY(${{(1-k)*24}}px)`;}});}}
function fade(el,a,t,d=0.5){{if(!el)return; const k=ease((t-a)/d); el.style.opacity=k; el.style.transform=`translateY(${{(1-k)*20}}px)`;}}
window.render=function(t){{
  document.querySelectorAll('.prog b').forEach((b,i)=>{{const [a,z]=SC[i]; b.style.width=(cl((t-a)/(z-a))*100)+'%';}});
  SC.forEach(([a,z],i)=>{{const s=document.getElementById('s'+(i+1));
    const vin=ease((t-a)/0.45), vout= i<3 ? 1-ease((t-(z-0.35))/0.35) : 1;
    s.style.opacity=Math.min(vin,vout); s.style.transform=`translateY(${{(1-vin)*40 - (1-vout)*40}}px)`;}});
  const s1=document.getElementById('s1');
  seq(s1.querySelectorAll('.h'),0.15,1.1,t); fade(s1.querySelector('.fade'),1.1,t); fade(s1.querySelector('.fade2'),1.5,t);
  const pop=s1.querySelector('.pop'); const k=ease((t-1.9)/0.5); pop.style.opacity=k; pop.style.transform=`scale(${{0.92+0.08*k}})`;
  [2,3].forEach(i=>{{const [a,z]=SC[i-1]; const s=document.getElementById('s'+i);
    seq(s.querySelectorAll('.k'),a+0.5,a+3.2,t); fade(s.querySelector('.fade'),a+3.2,t); fade(s.querySelector('.fade2'),a+3.7,t);}});
  const s4=document.getElementById('s4'), a=SC[3][0];
  seq(s4.querySelectorAll('.k'),a+0.4,a+1.9,t); fade(s4.querySelector('.fade'),a+2.0,t); fade(s4.querySelector('.fade2'),a+2.4,t);
  fade(s4.querySelector('.cta'),a+2.9,t); fade(s4.querySelector('.handle'),a+3.1,t);
  const br=s4.querySelector('.brand'); const kb=ease((t-(a+3.2))/0.5); br.style.opacity=kb; br.style.transform=`scale(${{0.85+0.15*kb}})`;
}};
</script></body></html>"""

CHECK = """() => { const bad=[];
 const box=(sel)=>document.querySelector(sel);
 const over=(el,limit)=> el && el.getBoundingClientRect().bottom > limit;
 if (over(box('#s1 .t-en'), 480)) bad.push('cover en title (reel: max 2 lines)');
 if (over(box('#s1 .t-ko'), 700)) bad.push('cover ko title');
 if (over(box('#s1 .t-mn'), 940)) bad.push('cover mn title');
 for (const id of ['s2','s3']) { if (over(box('#'+id+' .card'), 1500)) bad.push(id+' body too long for reel'); }
 if (over(box('#s4 .card'), 1280)) bad.push('summary too long for reel');
 return bad; }"""

async def render(p, out):
    tmp = tempfile.mkdtemp()
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={"width": W, "height": H})
        await pg.set_content(page(p)); await pg.wait_for_timeout(300)
        await pg.evaluate("render(30)")  # everything visible for overflow check
        await pg.evaluate("document.querySelectorAll('.scene').forEach(s=>{s.style.opacity=1;s.style.transform='none'})")
        bad = await pg.evaluate(CHECK)
        n = int(DUR * FPS)
        for i in range(n):
            await pg.evaluate(f"render({i / FPS})")
            await pg.screenshot(path=os.path.join(tmp, f"{i:05d}.jpg"), type="jpeg", quality=92)
        await b.close()
    mp4 = os.path.join(out, f"{p['slug']}-reel.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "%05d.jpg"),
                    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                    "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", mp4], check=True)
    shutil.rmtree(tmp)
    return mp4, bad

async def main():
    src, out = sys.argv[1], sys.argv[2]
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    os.makedirs(out, exist_ok=True)
    errors = []
    for p in json.load(open(src, encoding="utf-8")):
        if only and p["slug"] != only: continue
        if not all(k in p for k in ("what", "why", "summary")): continue
        mp4, bad = await render(p, out); print(mp4)
        if bad: errors.append(f"{p['slug']} reel: TEXT TOO LONG -> shorten: " + ", ".join(bad))
    if errors:
        print("\n".join(errors), file=sys.stderr); sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
