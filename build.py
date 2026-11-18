#!/usr/bin/env python3
"""Günlük Bültenim site generator.

Kullanım: python3 build.py <gunluk.json>
gunluk.json: {"news": {...}, "istanbul": {...}}  (o günün haber ve etkinlik verisi)
Kalıcı veriler: data/programs.json, data/events.json
Çıktı: index.html, archive/YYYY-MM-DD.html, archive/index.html
"""
import json, os, sys, html, glob
from datetime import datetime, date
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.abspath(__file__))
TZ = ZoneInfo("Europe/Istanbul")
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
         "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]


def e(s):
    return html.escape(str(s or ""), quote=True)


def tr_date(d, weekday=True):
    s = f"{d.day} {AYLAR[d.month - 1]} {d.year}"
    return s + (f" {GUNLER[d.weekday()]}" if weekday else "")


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


CSS = """
:root{--bg:#faf8f3;--card:#fff;--ink:#1d1d1f;--muted:#6b6b70;--line:#e4e0d6;--accent:#b3261e;
--accent-soft:#fdecea;--link:#0b57d0;--alert-bg:#fff4d6;--alert-line:#e0a100;--chip:#efece4;--closed:#9a9a9a}
@media (prefers-color-scheme:dark){:root{--bg:#121214;--card:#1c1c1f;--ink:#ececee;--muted:#a0a0a8;
--line:#2e2e33;--accent:#ff6b5e;--accent-soft:#3a1d1b;--link:#8ab4f8;--alert-bg:#2b2410;--alert-line:#d4a017;
--chip:#2a2a2e;--closed:#6c6c72}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 Georgia,'Times New Roman',serif}
a{color:var(--link)}
.wrap{max-width:1040px;margin:0 auto;padding:0 16px 48px}
header{text-align:center;border-bottom:3px double var(--ink);padding:28px 0 14px;margin-bottom:24px}
header h1{font-size:clamp(2rem,6vw,3.2rem);margin:0;letter-spacing:.02em}
header .meta{font-family:system-ui,sans-serif;color:var(--muted);font-size:.9rem;margin-top:6px}
h2{font-size:1.5rem;border-bottom:1px solid var(--line);padding-bottom:6px;margin:36px 0 16px}
.sans{font-family:system-ui,-apple-system,'Segoe UI',sans-serif}
.alert{background:var(--alert-bg);border:2px solid var(--alert-line);border-left-width:8px;border-radius:10px;padding:16px 18px}
.alert h2{margin-top:0;border:0;color:var(--ink)}
.alert ul{list-style:none;padding:0;margin:0;display:grid;gap:12px}
.alert li{background:var(--card);border-radius:8px;padding:12px 14px;border:1px solid var(--line)}
.alert .when{font-weight:700;color:var(--accent);font-family:system-ui,sans-serif;font-size:.9rem}
.alert .title{font-weight:700;font-size:1.08rem}
.alert .why{font-size:.95rem}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.card h3{margin:4px 0 6px;font-size:1.08rem;line-height:1.35}
.card p{margin:0 0 8px}
.tag{display:inline-block;font:600 .72rem/1 system-ui,sans-serif;text-transform:uppercase;letter-spacing:.06em;
background:var(--chip);color:var(--muted);padding:4px 7px;border-radius:4px}
.src{font:.85rem system-ui,sans-serif;color:var(--muted)}
.kur{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:14px;font-family:system-ui,sans-serif}
.kur div{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 14px}
.kur b{font-size:1.2rem}
.info{font:.88rem system-ui,sans-serif;color:var(--muted)}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.filters button{font:600 .9rem system-ui,sans-serif;border:1px solid var(--line);background:var(--card);color:var(--ink);
padding:6px 14px;border-radius:999px;cursor:pointer}
.filters button.on{background:var(--ink);color:var(--bg)}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--card)}
table{border-collapse:collapse;width:100%;font:.86rem/1.45 system-ui,sans-serif;min-width:980px}
th,td{padding:9px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:var(--chip);position:sticky;top:0}
tr.closed td{color:var(--closed)}
.badge{display:inline-block;font:700 .7rem/1 system-ui,sans-serif;padding:4px 6px;border-radius:4px;margin-top:4px}
.badge.soon{background:var(--accent);color:#fff}
.badge.closed{background:var(--chip);color:var(--closed)}
footer{margin-top:40px;text-align:center;font:.9rem system-ui,sans-serif;color:var(--muted)}
ul.arch{list-style:none;padding:0}ul.arch li{padding:8px 0;border-bottom:1px solid var(--line)}
"""

JS = """
document.querySelectorAll('.filters button').forEach(function(b){b.addEventListener('click',function(){
document.querySelectorAll('.filters button').forEach(function(x){x.classList.remove('on')});b.classList.add('on');
var f=b.dataset.f;document.querySelectorAll('#prog tbody tr').forEach(function(r){
r.style.display=(f==='all'||r.dataset.ulke===f||r.dataset.kat===f)?'':'none';});});});
"""


def page(title, body):
    return f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{e(title)}</title><style>{CSS}</style></head>
<body><div class="wrap">{body}</div></body></html>
"""


def build(daily_path):
    now = datetime.now(TZ)
    today = now.date()
    iso = today.isoformat()
    daily = load(daily_path, {})
    news = daily.get("news", {})
    ist = daily.get("istanbul", {})
    programs = load(os.path.join(ROOT, "data/programs.json"), {"programs": []})["programs"]
    events_all = load(os.path.join(ROOT, "data/events.json"), {"events": []})["events"]

    # Etkinlikler: yalnızca bugün ve sonrası
    events = sorted([x for x in events_all if (x.get("tarih") or "") >= iso], key=lambda x: x["tarih"])

    out = [f"""<header><h1>Günlük Bültenim</h1>
<div class="meta">{e(tr_date(today))} · Son güncelleme: {now:%H:%M} (TSİ)</div></header>"""]

    # Fırsat Etkinlikleri
    out.append('<section class="alert"><h2>🎯 Fırsat Etkinlikleri</h2>')
    if events:
        out.append("<ul>")
        for x in events:
            d = date.fromisoformat(x["tarih"])
            kalan = (d - today).days
            k = "Bugün!" if kalan == 0 else f"{kalan} gün kaldı"
            out.append(f"""<li><div class="when">{e(x.get('tarih_metin') or tr_date(d))} · {e(x.get('yer'))} · {k}</div>
<div class="title"><a href="{e(x['url'])}" target="_blank" rel="noopener">{e(x['baslik'])}</a></div>
<div class="why"><b>Neden önemli:</b> {e(x.get('neden_onemli'))}</div>
<div class="src">{e(x.get('kaynak'))}</div></li>""")
        out.append("</ul>")
    else:
        out.append("<p>Şu an kayıtlı yaklaşan etkinlik yok.</p>")
    out.append("</section>")

    # Dünün Özeti
    out.append(f"<section><h2>📰 Dünün Özeti <span class='info'>({e(tr_date(date.fromordinal(today.toordinal()-1)))})</span></h2>")
    kur = news.get("kur")
    if kur:
        out.append(f"""<div class="kur"><div>USD/TRY <b>{e(kur.get('usd_try'))}</b></div>
<div>EUR/TRY <b>{e(kur.get('eur_try'))}</b></div>
<div class="src" style="align-self:center">Kaynak: <a href="{e(kur.get('url'))}" target="_blank" rel="noopener">{e(kur.get('kaynak'))}</a>{(' · ' + e(kur.get('not'))) if kur.get('not') else ''}</div></div>""")
    out.append('<div class="grid">')
    for n in news.get("items", []):
        out.append(f"""<article class="card"><span class="tag">{e(n.get('kategori'))}</span>
<h3>{e(n.get('baslik'))}</h3><p>{e(n.get('ozet'))}</p>
<div class="src">Kaynak: <a href="{e(n.get('url'))}" target="_blank" rel="noopener">{e(n.get('kaynak'))}</a></div></article>""")
    out.append("</div></section>")

    # Bugün İstanbul'da
    out.append("<section><h2>🌉 Bugün İstanbul'da</h2><div class='grid'>")
    for x in ist.get("items", []):
        bits = [b for b in (x.get("saat"), x.get("mekan"), x.get("ucret")) if b]
        out.append(f"""<article class="card"><span class="tag">{e(x.get('tur'))}</span>
<h3>{e(x.get('baslik'))}</h3><p>{e(x.get('aciklama'))}</p>
<div class="src">{' · '.join(e(b) for b in bits)}</div>
<div class="src"><a href="{e(x.get('url'))}" target="_blank" rel="noopener">Detay ve bilet →</a></div></article>""")
    out.append("</div></section>")

    # Yüksek Lisans
    def key(p):
        d = p.get("son_tarih")
        if not d:
            return (2, "9999")
        return (0, d) if d >= iso else (3, d)
    programs = sorted(programs, key=key)
    out.append("""<section><h2>🎓 Yüksek Lisans Programları</h2>
<p class="info">Almanya ve Hollanda'da geomatik ve management programları · Sıralama: en yakın son tarih önce ·
Son tarihler non-EU (uluslararası) başvurular içindir; başvurmadan önce resmi sayfadan teyit edin.</p>
<div class="filters"><button class="on" data-f="all">Tümü</button><button data-f="Almanya">Almanya</button>
<button data-f="Hollanda">Hollanda</button><button data-f="Geomatik">Geomatik</button>
<button data-f="Management">Management</button></div>
<div class="tablewrap"><table id="prog"><thead><tr><th>Üniversite</th><th>Program</th><th>Ülke/Şehir</th><th>Dil</th>
<th>Başvuru dönemi / son tarih</th><th>Harç ücreti</th><th>Gerekli belgeler</th><th>Link</th></tr></thead><tbody>""")
    for p in programs:
        d = p.get("son_tarih")
        badge, cls = "", ""
        if d:
            kalan = (date.fromisoformat(d) - today).days
            if kalan < 0:
                badge, cls = '<br><span class="badge closed">Kapandı</span>', "closed"
            elif kalan <= 30:
                badge = f'<br><span class="badge soon">YAKLAŞIYOR · {kalan} gün</span>'
        out.append(f"""<tr class="{cls}" data-ulke="{e(p.get('ulke'))}" data-kat="{e(p.get('kategori'))}">
<td>{e(p.get('universite'))}</td><td><b>{e(p.get('program'))}</b><br><span class="tag">{e(p.get('kategori'))}</span></td>
<td>{e(p.get('ulke'))} / {e(p.get('sehir'))}</td><td>{e(p.get('dil'))}</td>
<td>{e(p.get('basvuru_donemi'))}{badge}</td><td>{e(p.get('harc'))}</td><td>{e(p.get('belgeler'))}</td>
<td><a href="{e(p.get('url'))}" target="_blank" rel="noopener">Sayfa</a></td></tr>""")
    out.append(f"</tbody></table></div><p class='info'>{len(programs)} program listeleniyor.</p></section>")
    out.append(f"<script>{JS}</script>")
    out.append('<footer><a href="ROOTarchive/index.html">📚 Arşiv – önceki bültenler</a></footer>')

    body = "\n".join(out)
    title = f"Günlük Bültenim – {tr_date(today, False)}"
    os.makedirs(os.path.join(ROOT, "archive"), exist_ok=True)
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(title, body.replace("ROOTarchive/", "archive/")))
    with open(os.path.join(ROOT, "archive", f"{iso}.html"), "w", encoding="utf-8") as f:
        f.write(page(title, body.replace("ROOTarchive/", "")))

    days = sorted((os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, "archive/????-??-??.html"))), reverse=True)
    items = "".join(f'<li><a href="{d}.html">{e(tr_date(date.fromisoformat(d)))}</a></li>' for d in days)
    with open(os.path.join(ROOT, "archive", "index.html"), "w", encoding="utf-8") as f:
        f.write(page("Arşiv – Günlük Bültenim", f"""<header><h1>Arşiv</h1><div class="meta">Günlük Bültenim – tüm günler</div></header>
<p><a href="../index.html">← Bugünün bülteni</a></p><ul class="arch">{items}</ul>"""))
    open(os.path.join(ROOT, ".nojekyll"), "a").close()


if __name__ == "__main__":
    build(sys.argv[1])
