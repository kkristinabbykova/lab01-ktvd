"""Собрать лендинг docs/index.html из данных работы (GitHub Pages публикует папку docs/).

    python tools/build_landing.py            # или через tools/build_site.py вместе с экспортом marimo

Страница самодостаточная: данные (квантили pH, измерения шрифтов) встраиваются как JSON,
живой датчик pH работает на чистом JavaScript. Если рядом есть docs/datchik/ (экспорт
marimo), страница ссылается на него.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
REPO = os.environ.get("LAB_REPO_URL", "").rstrip("/")   # этот репозиторий: https://github.com/<логин>/<репо>
MAIN = os.environ.get("LAB_MAIN_URL", "").rstrip("/")   # общий репозиторий команды с lab01.ipynb (необязательно)


def wine_block():
    w = pd.read_csv(ROOT / "data" / "winequality-white.csv", sep=";")
    x = np.sort(w["pH"].to_numpy())
    p = (np.arange(1, x.size + 1) - 0.5) / x.size
    q = np.interp(np.linspace(0, 1, 201), p, x)
    edges = np.arange(2.705, 3.845, 0.02)
    h, _ = np.histogram(x, bins=edges, density=True)
    rows = []
    for col, nm, unit in (("pH", "pH", "ед. pH"), ("fixed acidity", "фиксированная кислотность", "г/дм³"),
                          ("alcohol", "спирт", "% об.")):
        v = w[col]
        rows.append({"name": nm, "unit": unit, "mean": round(v.mean(), 3), "sd": round(v.std(), 3),
                     "skew": round(float(stats.skew(v)), 2)})
    grid = np.round(np.arange(2.50, 4.21, 0.01), 2)          # сетка шага прибора 0.01
    fdat = np.searchsorted(np.round(x, 2), grid + 1e-9, side="right") / x.size
    return {"grid": [float(g) for g in grid], "fdat": [round(float(v), 6) for v in fdat],
            "q": [round(float(v), 4) for v in q], "edges": [round(float(e), 3) for e in edges],
            "hist": [round(float(v), 4) for v in h], "n": int(x.size), "rows": rows}


def fonts_block():
    f = pd.read_csv(ROOT / "data" / "fonts.csv")
    f["category"] = f["category"].fillna("")
    f = f[~f.no_lowercase]
    import csv
    src = {r["family_folder"].replace("_", " "): r["source"]
           for r in csv.DictReader(open(ROOT / "data" / "font_categories.csv", encoding="utf-8"))}
    num = lambda v, d=4: None if pd.isna(v) else round(float(v), d)   # noqa: E731
    pts = [{"f": r.family, "c": r.category, "x": num(r.x_height), "s": num(r.stem), "cap": num(r.cap_height),
            "ct": num(r.contrast, 2), "w": num(r.width_o, 3), "g": "Google Fonts" in src.get(r.family, "Google Fonts")}
           for r in f.itertuples()]
    med = f.groupby("category").x_height.median().round(3).to_dict()
    rho = stats.spearmanr(f.x_height, f.stem)[0]
    stems = sorted(round(float(v), 4) for v in f.stem)
    return {"pts": pts, "med": med, "rho": round(float(rho), 2), "n": len(f), "stems": stems}


def link(path, text):
    return f'<a href="{REPO}/blob/main/{path}">{text}</a>' if REPO else f"<code>{path}</code>"


def main():
    DOCS.mkdir(exist_ok=True)
    (DOCS / "img").mkdir(exist_ok=True)
    for name in ("rv01_rv02_dependence.png", "fonts_measure.png", "rv01_eda.png"):
        if (ROOT / "figures" / name).exists():
            shutil.copy(ROOT / "figures" / name, DOCS / "img" / name)
    data = {"wine": wine_block(), "fonts": fonts_block()}
    has_marimo = (DOCS / "datchik" / "index.html").exists()
    marimo = ('<a class="button" href="datchik/">Открыть полный датчик</a>' if has_marimo else
              '<span class="note">Полная версия на marimo появится здесь после команды '
              '<code>python tools/build_site.py</code>.</span>')
    html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False)) \
        .replace("__MARIMO__", marimo) \
        .replace("__L_NB__", f' (<a href="{MAIN}">репозиторий</a>)' if MAIN else "") \
        .replace("__L_FONTS__", link("fonts.ipynb", "fonts.ipynb")) \
        .replace("__L_DATCHIK__", link("datchik.py", "datchik.py")) \
        .replace("__N_FONTS__", str(data["fonts"]["n"])) \
        .replace("__RHO__", f"{data['fonts']['rho']:.2f}".replace(".", ",")) \
        .replace("__XH_SANS__", f"{data['fonts']['med'].get('sans', float('nan')):.3f}".replace(".", ",")) \
        .replace("__XH_SERIF__", f"{data['fonts']['med'].get('serif', float('nan')):.3f}".replace(".", ","))
    (DOCS / "index.html").write_text(html, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("")
    print("docs/index.html собран", "(есть marimo-датчик)" if has_marimo else "(без marimo-экспорта)")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lab01 КТвД: шрифт как случайная величина</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Golos+Text:wght@400..900&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Roboto+Flex:opsz,wdth,wght@8..144,25..151,100..1000&display=swap" rel="stylesheet">
<style>
:root{
  --paper:#f6f7f5; --ink:#1a1d24; --muted:#5c6170; --rule:#dcdfd8;
  --blue:#2a78d6; --orange:#eb6834; --straw:#d8c56a; --green:#1baf7a;
  --measure:68ch;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);
  font:400 1.0625rem/1.6 "Golos Text",system-ui,-apple-system,"Segoe UI",sans-serif;}
a{color:var(--blue);text-underline-offset:.18em}
a:focus-visible,button:focus-visible,select:focus-visible,input:focus-visible,circle:focus-visible{outline:3px solid var(--orange);outline-offset:3px}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.88em;background:#e9ebe6;padding:.08em .35em;border-radius:3px}
.wrap{max-width:1120px;margin:0 auto;padding:0 clamp(1.1rem,4vw,2.5rem)}
.text{max-width:var(--measure)}

/* --- hero: толщина каждой буквы — случайная величина --- */
header.wrap{padding-top:clamp(3rem,9vw,7rem);padding-bottom:clamp(3.5rem,7vw,5.5rem)}
h1{font-size:clamp(2.9rem,9.2vw,7.4rem);line-height:.98;letter-spacing:-.02em;margin:0 0 1.6rem;font-weight:400}
h1 .w{display:block}
h1 span.l{transition:font-weight .5s cubic-bezier(.2,.7,.2,1)}
.lede{font-size:clamp(1.1rem,1.6vw,1.3rem);color:var(--muted);margin:0 0 1.4rem}
.strip{height:10px;border-radius:5px;margin:2.6rem 0 0;
  background:linear-gradient(90deg,#c0392b 0%,var(--orange) 22%,var(--straw) 45%,var(--green) 66%,var(--blue) 100%)}
.strip-caption{display:flex;justify-content:space-between;color:var(--muted);font-size:.85rem;margin-top:.4rem}
button,.button{font:inherit;font-weight:600;font-size:.98rem;background:var(--ink);color:var(--paper);
  border:0;border-radius:999px;padding:.62rem 1.15rem;cursor:pointer;text-decoration:none;display:inline-block}
button:hover,.button:hover{background:#353a46}
.note{color:var(--muted);font-size:.95rem}

/* --- секции --- */
section.wrap{padding-top:3.5rem;padding-bottom:3.5rem;border-top:1px solid var(--rule)}
h2{font-size:clamp(1.7rem,3.4vw,2.6rem);line-height:1.1;font-weight:750;letter-spacing:-.01em;margin:0 0 1rem}
h3{font-size:1.15rem;font-weight:650;margin:2rem 0 .5rem}
p{margin:0 0 1rem}
figure{margin:1.8rem 0}
figure img{width:100%;max-width:760px;height:auto;background:#fff;border-radius:6px}
figure.wide img{max-width:100%}
figcaption{color:var(--muted);font-size:.92rem;margin-top:.5rem;max-width:var(--measure)}

.scroll{overflow-x:auto;max-width:100%}
table{border-collapse:collapse;width:100%;max-width:820px;font-variant-numeric:tabular-nums;margin:1.2rem 0}
th,td{text-align:left;padding:.55rem .8rem .55rem 0;border-bottom:1px solid var(--rule)}
th{font-weight:600;color:var(--muted);font-size:.92rem}
td.num{text-align:right}

/* --- живой датчик --- */
.lab{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(0,1fr);gap:1.6rem;align-items:start;margin-top:1.4rem}
.controls{display:flex;flex-wrap:wrap;gap:1rem 1.4rem;align-items:end;margin:1.2rem 0 .4rem}
label{display:flex;flex-direction:column;gap:.3rem;font-size:.9rem;color:var(--muted)}
select,input[type=range]{font:inherit;color:var(--ink)}
select:not(.fancy){padding:.4rem .5rem;border:1px solid #c9cdc5;border-radius:6px;background:#fff}
.chart{background:#fff;border-radius:8px;padding:.6rem}
.chart svg,.chart canvas{display:block;width:100%;height:auto}
.readout{font-variant-numeric:tabular-nums;margin-top:.7rem;font-size:.95rem}
.readout b{font-weight:650}
.legend{display:flex;flex-wrap:wrap;gap:.4rem 1rem;font-size:.88rem;color:var(--muted);margin:.5rem 0 0}
.sw{display:inline-block;width:.8em;height:.8em;border-radius:2px;margin-right:.35em;vertical-align:-.05em}

/* --- шрифты --- */
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1.4rem 2rem;margin:1.6rem 0;max-width:900px}
.fact strong{display:block;font-size:2.4rem;line-height:1.05;font-weight:800;font-variant-numeric:tabular-nums}
.fact span{color:var(--muted);font-size:.95rem}
.zoombar{display:flex;gap:.4rem;align-items:center;margin:0 0 .4rem;flex-wrap:wrap}
.zoombar button{font:inherit;font-size:.95rem;min-width:2.2rem;height:2.2rem;padding:0 .7rem;border-radius:6px;border:1px solid #d6d4cc;background:#fff;color:var(--ink);cursor:pointer}
.zoombar button:hover{background:#f3f2ee}.zoombar button:focus-visible{outline:2px solid #2a78d6;outline-offset:2px}
.zoombar .note{margin:0 0 0 .4rem}
#scatter{user-select:none;-webkit-user-select:none}
#zoomHint{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);background:rgba(26,29,36,.82);color:#fff;padding:.5rem .8rem;border-radius:6px;font-size:.9rem;pointer-events:none;opacity:0;transition:opacity .25s}
#tip{position:absolute;pointer-events:none;background:var(--ink);color:var(--paper);font-size:.85rem;
  padding:.3rem .55rem;border-radius:4px;opacity:0;transition:opacity .12s;white-space:nowrap}
footer.wrap{padding-top:3rem;padding-bottom:4rem;border-top:1px solid var(--rule);color:var(--muted);font-size:.95rem}
footer p{max-width:var(--measure)}

.specimen{padding:1.2rem 1.4rem;overflow:hidden}
.rho-demo{margin:0 0 2rem}
.rho-grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem;max-width:820px}
.rho-grid svg{width:100%;height:auto;display:block}
#rhoPresets button[aria-pressed="true"]{background:#fff;font-weight:650;box-shadow:0 1px 3px rgba(26,29,36,.18)}
@media (max-width:560px){.rho-grid{grid-template-columns:1fr}}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.seg{display:inline-flex;flex-wrap:wrap;gap:2px;background:#e6e8e3;border-radius:999px;padding:3px}
.seg button{background:transparent;color:var(--ink);font-weight:500;font-size:.92rem;padding:.42rem .95rem;border-radius:999px;transition:background .15s}
.seg button:hover{background:#f2f3f0}
.seg button[aria-checked="true"]{background:#fff;font-weight:650;box-shadow:0 1px 3px rgba(26,29,36,.18)}
.fancy{appearance:none;-webkit-appearance:none;font:inherit;font-size:.95rem;color:var(--ink);background:#fff
  url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' fill='none' stroke='%231a1d24' stroke-width='1.6'/%3E%3C/svg%3E") no-repeat right .9rem center;
  border:1px solid #c9cdc5;border-radius:999px;padding:.5rem 2.2rem .5rem .95rem;min-width:12rem;cursor:pointer}
.fancy:hover{border-color:#9aa0a8}
#play .controls label{min-width:11rem;flex:1 1 11rem}
#play .controls label .val{color:var(--ink);font-weight:600;font-variant-numeric:tabular-nums}
#play .controls input[type=range]{width:100%}
#flex{font-family:"Roboto Flex","Golos Text",system-ui,sans-serif;line-height:1.05;outline:none;word-break:break-word;min-height:1.2em}
#flex:focus-visible{box-shadow:0 0 0 3px var(--orange);border-radius:4px}
input[type=text]{font:inherit;font-size:.95rem;color:var(--ink);padding:.5rem .95rem;border:1px solid #c9cdc5;border-radius:999px;background:#fff}
input[type=text]:hover{border-color:#9aa0a8}
.controls label .val{color:var(--ink);font-weight:600;font-variant-numeric:tabular-nums}
.cmp-row{background:#fff;border-radius:8px;padding:.8rem 1rem 1rem;margin:0 0 1rem}
.cmp-row svg{display:block;width:100%;height:auto}
.cmp-head{display:flex;justify-content:space-between;align-items:baseline;gap:1rem;flex-wrap:wrap;margin-bottom:.3rem}
.cmp-head b{font-weight:650}
.bars{display:grid;grid-template-columns:repeat(auto-fit,minmax(11rem,1fr));gap:.6rem 1.4rem;margin-top:.6rem}
.bar{font-size:.85rem;color:var(--muted)}
.bar .track{position:relative;height:8px;border-radius:4px;background:#eceee9;margin-top:.25rem}
.bar .fill{position:absolute;left:0;top:0;bottom:0;border-radius:4px}
.bar .med{position:absolute;top:-3px;bottom:-3px;width:2px;background:var(--ink);opacity:.55}
@media (max-width:760px){.lab{grid-template-columns:1fr} th,td{padding-right:.6rem;font-size:.95rem}}
@media (prefers-reduced-motion:reduce){h1 span.l{transition:none}}
</style>
</head>
<body>
<header class="wrap">
  <h1 id="title" aria-label="Шрифт как случайная величина"><span class="w">Шрифт как</span><span class="w">случайная</span><span class="w">величина</span></h1>
  <p class="lede text">Это доп. задание КТвД к лабораторной по прикладной статистике. Я собрала датасет шрифтов
  с Google Fonts (в анализе их __N_FONTS__: часть выбрана мной, остальные добавлены случайным отбором, по 20 в каждой категории)
  и измерила у каждого две вещи: высоту строчных букв (x-height) и толщину штриха.
  Эти размеры нельзя вычислить по формуле — у каждого шрифта они свои, поэтому их можно изучать как случайные величины.</p>
  <p class="lede text">Ниже — что получилось и интерактивный датчик, который выдаёт случайные числа, похожие на настоящие данные.
  Нажми кнопку: толщина каждой буквы в заголовке выпадет случайно, из тех же значений, что у настоящих шрифтов.</p>
  <button id="reroll" type="button">Перебросить толщину букв</button>
</header>

<main>
<section class="wrap" id="fonts">
  <h2>Шрифты: высота строчных и толщина штриха</h2>
  <div class="text">
  <p>Датасет собран самостоятельно: __N_FONTS__ шрифтовых семейств из Google Fonts, по 20 гротесков, антикв, акцидентных,
  рукописных и моноширинных. У каждого измерено начертание Regular прямо по контурам букв. Все размеры даны в долях кегля, то есть не зависят от размера, которым набран текст.</p>
  </div>
  <figure class="wide">
    <img src="img/fonts_measure.png" alt="Буквы H x l n o шрифта Playfair с линиями измерений" loading="lazy">
    <figcaption>Что измеряется: x-height (верх строчной «x»), высота прописных, толщина вертикали «l» и контраст «o».</figcaption>
  </figure>
  <div class="facts">
    <div class="fact"><strong>__XH_SANS__</strong><span>медианная x-height гротесков</span></div>
    <div class="fact"><strong>__XH_SERIF__</strong><span>медианная x-height антикв: строчные ниже, критерий Манна–Уитни это подтверждает</span></div>
    <div class="fact"><strong>ρ = __RHO__</strong><span>связь x-height и толщины штриха: чем выше строчные, тем толще штрих</span></div>
  </div>
  <div class="rho-demo">
    <h3>Как читать ρ</h3>
    <p class="note" style="max-width:var(--measure)">ρ Спирмена показывает, насколько согласованно растут две величины: 0 — связи нет,
    1 — чем больше одна, тем больше другая, без исключений. Подвигай ползунок: слева облако из 100 случайных точек с выбранной
    силой связи, справа — наши шрифты (ρ = __RHO__).</p>
    <div class="controls" style="margin-top:.4rem">
      <label style="min-width:16rem"><span>Сила связи ρ: <output id="rhoOut" class="val">0,40</output></span>
        <input id="rho" type="range" min="-1" max="1" step="0.05" value="0.4" style="width:100%"></label>
      <span class="seg" id="rhoPresets" role="group" aria-label="Готовые значения">
        <button type="button" data-v="0">нет связи</button><button type="button" data-v="0.4">как у нас</button><button type="button" data-v="0.9">сильная</button></span>
    </div>
    <div class="rho-grid">
      <div class="chart"><svg id="rhoSim" viewBox="0 0 300 240" role="img" aria-label="Облако точек с выбранной силой связи"></svg>
        <p class="note" id="rhoSimNote" style="margin:.3rem 0 0"></p></div>
      <div class="chart"><svg id="rhoReal" viewBox="0 0 300 240" role="img" aria-label="Наши шрифты в рангах"></svg>
        <p class="note" style="margin:.3rem 0 0">Наши шрифты: место по x-height и место по толщине штриха (ранги, как у Спирмена).</p></div>
    </div>
  </div>
  <div class="chart" style="position:relative;max-width:820px">
    <div class="zoombar"><button type="button" id="zIn" aria-label="Приблизить">+</button><button type="button" id="zOut" aria-label="Отдалить">−</button><button type="button" id="zReset">Весь график</button><span id="zoomInfo" class="note"></span></div>
    <svg id="scatter" viewBox="0 0 640 380" role="img" aria-label="Точечный график: x-height и толщина штриха по шрифтам"></svg>
    <div id="zoomHint">Чтобы приблизить, держите Ctrl (⌘) и крутите колесо</div>
    <div id="tip" role="status"></div>
    <div class="legend" id="flegend"></div>
  </div>
  <p class="note">Приближайте кнопками «+ / −», двойным щелчком по месту, Ctrl (⌘) + колесом или двумя пальцами на телефоне; приближенный график можно двигать мышью. Когда точек на экране немного, у них появляются названия шрифтов. Наведите на точку или выберите её клавишей Tab, чтобы увидеть подробности. Исследование: __L_FONTS__.</p>
</section>

<section class="wrap" id="play">
  <h2>Попробуй сам</h2>
  <h3>Толщина и ширина</h3>
  <div class="text">
  <p>Этот текст набран вариативным шрифтом Roboto Flex: у него толщину штриха и ширину букв можно менять плавно.
  Подвигай ползунки и посмотри, как меняется характер текста. Текст можно исправить — просто нажми на него.</p>
  </div>
  <div class="controls">
    <label><span>Толщина (вес): <output id="wghtOut" class="val">400</output></span>
      <input id="wght" type="range" min="100" max="1000" step="10" value="400"></label>
    <label><span>Ширина: <output id="wdthOut" class="val">100</output><span class="val">&nbsp;%</span></span>
      <input id="wdth" type="range" min="25" max="151" step="1" value="100"></label>
    <label><span>Кегль: <output id="sizeOut" class="val">72</output><span class="val">&nbsp;px</span></span>
      <input id="size" type="range" min="16" max="160" step="2" value="72"></label>
    <button id="resetPlay" type="button">Сбросить</button>
  </div>
  <div class="chart specimen"><div id="flex" contenteditable="true" spellcheck="false" aria-label="Образец текста, можно редактировать">Шрифт как случайная величина</div></div>
  <p class="note" id="flexNote"></p>

  <h3>Сравнение шрифтов</h3>
  <div class="text">
  <p>Выбери до трёх шрифтов из датасета и введи любой текст. Все строки набраны одним кеглем: сразу видно, у какого
  шрифта строчные выше и штрих толще. Пунктир — наши измерения: высота строчных (x-height) и прописных.</p>
  </div>
  <div class="controls">
    <label>Шрифт 1 <select class="fpick fancy" data-i="0"></select></label>
    <label>Шрифт 2 <select class="fpick fancy" data-i="1"></select></label>
    <label>Шрифт 3 <select class="fpick fancy" data-i="2"></select></label>
    <label style="flex:1;min-width:14rem">Текст <input id="cmpText" type="text" value="Hxlno шрифт" maxlength="40"></label>
  </div>
  <div id="cmp"></div>
</section>

<section class="wrap" id="rng">
  <h2>Датчик: случайное число, похожее на pH</h2>
  <div class="text">
  <p>Это датчик из спринта 2. pH белого вина описан логнормальным распределением со сдвигом:
  <i>X</i> = θ + e<sup>μ + σ<i>Z</i></sup>, где <i>Z</i> — стандартное нормальное число. Нормальные числа получаются
  полярным методом Марсальи: точка бросается в квадрат, и остаются только точки внутри круга.
  Для сравнения можно включить квантильное преобразование по самим данным.</p>
  </div>
  <div class="controls">
    <label><span id="methodLab">Метод</span>
      <span class="seg" data-for="method" role="radiogroup" aria-labelledby="methodLab"></span>
      <select id="method" class="sr" tabindex="-1" aria-hidden="true">
        <option value="polar">Полярный (спринт 2)</option>
        <option value="quantile">Квантильный</option>
      </select>
    </label>
    <label><span id="baseLab">Базовый датчик</span>
      <span class="seg" data-for="base" role="radiogroup" aria-labelledby="baseLab"></span>
      <select id="base" class="sr" tabindex="-1" aria-hidden="true">
        <option value="math">Math.random</option>
        <option value="mmix">ЛКГ MMIX</option>
        <option value="randu">RANDU</option>
      </select>
    </label>
    <label style="min-width:12rem"><span>Сколько чисел: <output id="nout" class="val">4900</output></span>
      <input id="n" type="range" min="100" max="20000" step="100" value="4900" style="width:100%">
    </label>
    <button id="go" type="button">Сгенерировать заново</button>
  </div>
  <div class="lab">
    <div class="chart">
      <svg id="hist" viewBox="0 0 640 300" role="img" aria-label="Гистограмма pH: данные и датчик"></svg>
      <div class="legend"><span><i class="sw" style="background:#bcd6f3"></i>данные, 4898 вин</span><span><i class="sw" style="background:var(--orange)"></i>датчик (округлён до 0,01, как прибор)</span></div>
    </div>
    <div>
      <div class="chart"><canvas id="trip" width="520" height="520" aria-label="Точки базового датчика"></canvas></div>
      <p class="note" style="margin-top:.5rem" id="tripnote"></p>
    </div>
  </div>
  <p class="readout" id="readout"></p>
  <p>__MARIMO__</p>
  <p class="note">Данные о винах взяты из общей работы команды__L_NB__. В полной версии на marimo шесть методов для трёх величин вина и таблица сравнения: __L_DATCHIK__.</p>
</section>
</main>

<footer class="wrap">
  <p>Быкова Кристина Денисовна, ИСУ 501322, группа 27, трек КТвД. Lab01, прикладная статистика, осень 2026:
  датасет шрифтов, датчик pH (спринт 2), интерактив и этот сайт. Данные о винах — общая работа команды
  с Нефедьевой Антониной Сергеевной (трек «Инфохимия»).</p>
  <p>Данные: Wine Quality, UCI ML Repository, DOI 10.24432/C56S3T; шрифты: Google Fonts (SIL OFL).</p>
</footer>

<script>
const D = __DATA__;
const CAT = {sans:["гротески","#2a78d6"], serif:["антиквы","#eb6834"], display:["акцидентные","#1baf7a"],
             handwriting:["рукописные","#9b59b6"], mono:["моноширинные","#5c6170"]};
const nf = (v, d=3) => v.toFixed(d).replace(".", ",");

/* --- заголовок: вес буквы = квантиль толщины штриха --- */
const title = document.getElementById("title");
const stems = D.fonts.stems, sMin = stems[0], sMax = stems[stems.length - 1];
title.querySelectorAll(".w").forEach(w => {
  w.innerHTML = [...w.textContent].map(ch => ch === " " ? " " : `<span class="l" aria-hidden="true">${ch}</span>`).join("");
});
function reroll() {
  title.querySelectorAll("span.l").forEach(s => {
    const st = stems[Math.floor(Math.random() * stems.length)];
    // ранг толщины среди шрифтов -> вес 400..900
    const r = stems.indexOf(st) / (stems.length - 1);
    s.style.fontWeight = Math.round(400 + 500 * r);
    s.title = `толщина штриха ${nf(st)}`;
  });
}
document.getElementById("reroll").addEventListener("click", reroll);
reroll();

/* --- базовые датчики --- */
function makeBase(kind, seed = 2026) {
  if (kind === "randu") { let x = (seed | 1) >>> 0; return () => (x = Number((65539n * BigInt(x)) % 2147483648n)) / 2147483648; }
  if (kind === "mmix") {
    let x = BigInt(seed); const a = 6364136223846793005n, c = 1442695040888963407n, m = (1n << 64n) - 1n;
    return () => { x = (a * x + c) & m; return (Number(x >> 11n) + 0.5) / 9007199254740992; };
  }
  return Math.random;
}
const Q = D.wine.q;
function quantile(u) {           // эмпирическая F^-1 с линейной интерполяцией
  const t = u * (Q.length - 1), i = Math.min(Math.floor(t), Q.length - 2);
  return Q[i] + (t - i) * (Q[i + 1] - Q[i]);
}

/* --- полярный метод Марсальи (спринт 2): pH = theta + exp(mu + sigma*Z) --- */
const TH = 2.0877, MU = Math.log(1.0904), SG = 0.1363;
function polarPH(u, n) {
  const out = []; let tried = 0, acc = 0; const pts = [];
  while (out.length < n) {
    const v1 = 2 * u() - 1, v2 = 2 * u() - 1, s = v1 * v1 + v2 * v2;
    tried++;
    if (pts.length < 1500) pts.push([v1, v2, s > 0 && s < 1]);
    if (s > 0 && s < 1) {
      acc++;
      const f = Math.sqrt(-2 * Math.log(s) / s);
      out.push(TH + Math.exp(MU + SG * v1 * f), TH + Math.exp(MU + SG * v2 * f));
    }
  }
  return {x: out.slice(0, n), acc: acc / tried, pts};
}

/* --- гистограмма --- */
const NS = "http://www.w3.org/2000/svg";
const el = (tag, attrs) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; };
const E = D.wine.edges, H = D.wine.hist;
const W = 640, Hh = 300, pad = {l: 64, r: 12, t: 12, b: 40};   // слева место под числа оси и подпись
const xs = v => pad.l + (v - E[0]) / (E[E.length - 1] - E[0]) * (W - pad.l - pad.r);
const yMax = Math.max(...H) * 1.25;
const ys = v => Hh - pad.b - v / yMax * (Hh - pad.t - pad.b);
const svg = document.getElementById("hist");
function axes(s, xticks, yticks, xlab, ylab, X, Y, w, h, xd = 2, yd = 0) {
  xticks.forEach(t => { s.append(el("line", {x1: X(t), x2: X(t), y1: pad.t, y2: h - pad.b, stroke: "#e6e5e0"}));
    const tx = el("text", {x: X(t), y: h - pad.b + 18, "text-anchor": "middle", "font-size": 12, fill: "#5c6170"}); tx.textContent = nf(t, xd); s.append(tx); });
  yticks.forEach(t => { s.append(el("line", {x1: pad.l, x2: w - pad.r, y1: Y(t), y2: Y(t), stroke: "#e6e5e0"}));
    const tx = el("text", {x: pad.l - 8, y: Y(t) + 4, "text-anchor": "end", "font-size": 12, fill: "#5c6170"}); tx.textContent = nf(t, yd); s.append(tx); });
  const xl = el("text", {x: (pad.l + w - pad.r) / 2, y: h - 6, "text-anchor": "middle", "font-size": 13, fill: "#1a1d24"}); xl.textContent = xlab; s.append(xl);
  const yl = el("text", {x: 14, y: (pad.t + h - pad.b) / 2, "text-anchor": "middle", "font-size": 13, fill: "#1a1d24", transform: `rotate(-90 14 ${(pad.t + h - pad.b) / 2})`}); yl.textContent = ylab; s.append(yl);
}
function drawHist(gen) {
  svg.replaceChildren();
  axes(svg, [2.8, 3.0, 3.2, 3.4, 3.6, 3.8], [0, 1, 2, 3], "pH, ед. pH", "плотность", xs, ys, W, Hh);
  H.forEach((v, i) => svg.append(el("rect", {x: xs(E[i]) + .5, y: ys(v), width: Math.max(0, xs(E[i + 1]) - xs(E[i]) - 1), height: ys(0) - ys(v), fill: "#bcd6f3"})));
  const cnt = new Array(H.length).fill(0), bw = E[1] - E[0];
  gen.forEach(v => { const i = Math.floor((v - E[0]) / bw); if (i >= 0 && i < cnt.length) cnt[i]++; });
  let d = "";
  cnt.forEach((c, i) => { const y = ys(c / gen.length / bw); d += `${i ? "L" : "M"}${xs(E[i])},${y}L${xs(E[i + 1])},${y}`; });
  svg.append(el("path", {d, fill: "none", stroke: "#eb6834", "stroke-width": 2}));
}

/* --- тройки --- */
const cv = document.getElementById("trip"), ctx = cv.getContext("2d");
function drawPolar(pts) {
  ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, cv.width, cv.height);
  const S = cv.width - 40, cx = 20 + S / 2, cy = 20 + S / 2;
  ctx.strokeStyle = "#e6e5e0"; ctx.strokeRect(20.5, 20.5, S, S);
  ctx.strokeStyle = "#5c6170"; ctx.beginPath(); ctx.arc(cx, cy, S / 2, 0, 2 * Math.PI); ctx.stroke();
  pts.forEach(([a, b, ok]) => { ctx.fillStyle = ok ? "#2a78d6" : "#eb6834";
    ctx.fillRect(cx + a * S / 2 - 1.2, cy - b * S / 2 - 1.2, 2.6, 2.6); });
}
function drawTriples(kind) {
  const u = makeBase(kind, 7), n = 3000, a = [];
  for (let i = 0; i < n + 2; i++) a.push(u());
  ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, cv.width, cv.height);
  ctx.strokeStyle = "#e6e5e0"; ctx.strokeRect(20.5, 20.5, cv.width - 40, cv.height - 40);
  ctx.fillStyle = "rgba(26,29,36,.55)";
  for (let k = 0; k < n; k++) {
    const x = ((6 * a[k + 1] - 9 * a[k]) % 1 + 1) % 1, y = a[k + 2];
    ctx.fillRect(20 + x * (cv.width - 40), cv.height - 20 - y * (cv.height - 40), 2.2, 2.2);
  }
}

/* --- запуск --- */
const nIn = document.getElementById("n"), nOut = document.getElementById("nout"), baseIn = document.getElementById("base");
const methodIn = document.getElementById("method"), tripNote = document.getElementById("tripnote");
function run() {
  const n = +nIn.value, u = makeBase(baseIn.value, 2026 + Math.floor(Math.random() * 1e6));
  let gen, accTxt = "";
  if (methodIn.value === "polar") {
    const r = polarPH(u, n);
    gen = r.x.map(v => Math.round(v * 100) / 100);   // шаг прибора 0,01
    drawPolar(r.pts);
    tripNote.innerHTML = "Полярный метод: синие точки внутри круга приняты, оранжевые в углах отброшены.";
    accTxt = ` Доля принятых точек <b>${nf(r.acc)}</b> (теория π/4 = 0,785).`;
  } else {
    gen = Array.from({length: n}, () => Math.round(quantile(u()) * 100) / 100);
    drawTriples(baseIn.value);
    tripNote.innerHTML = "Тройки чисел базового датчика в проекции (6<i>u</i><sub>k+1</sub> − 9<i>u</i><sub>k</sub>) mod 1 по горизонтали и <i>u</i><sub>k+2</sub> по вертикали. У RANDU все точки ложатся на прямую: это его известный дефект.";
  }
  drawHist(gen);
  const m = gen.reduce((s, v) => s + v, 0) / n, sd = Math.sqrt(gen.reduce((s, v) => s + (v - m) ** 2, 0) / (n - 1));
  const sorted = gen.slice().sort((p, q) => p - q);
  const N0 = D.wine.n, crit = 1.358 * Math.sqrt((n + N0) / (n * N0));   // критическое значение КС, alpha = 0.05
  let D_ = 0;   // D Колмогорова: обе ЭФР на сетке шага прибора 0,01 (значения датчика округлены до 0,01)
  D.wine.grid.forEach((g, i) => { let lo = 0, hi = n; while (lo < hi) { const mid = (lo + hi) >> 1; sorted[mid] <= g + 1e-9 ? lo = mid + 1 : hi = mid; }
    D_ = Math.max(D_, Math.abs(lo / n - D.wine.fdat[i])); });
  document.getElementById("readout").innerHTML =
    `Датчик: среднее <b>${nf(m)}</b>, СКО <b>${nf(sd)}</b>; данные: среднее <b>3,188</b>, СКО <b>0,151</b>. ` +
    `Расстояние Колмогорова между функциями распределения <b>${nf(D_)}</b> при пороге <b>${nf(crit)}</b> (α = 0,05): ` +
    (D_ < crit ? "датчик и данные статистически не различаются." : "различие значимо.") + accTxt;
}
nIn.addEventListener("input", () => { nOut.textContent = nIn.value; });
nIn.addEventListener("change", run);
baseIn.addEventListener("change", run);
methodIn.addEventListener("change", run);
document.getElementById("go").addEventListener("click", run);
run();

/* --- переключатели-«таблетки» вместо выпадающих списков с 2–3 вариантами --- */
document.querySelectorAll(".seg[data-for]").forEach(seg => {
  const sel = document.getElementById(seg.dataset.for);
  const btns = [...sel.options].map(o => {
    const b = document.createElement("button");
    b.type = "button"; b.textContent = o.textContent; b.setAttribute("role", "radio"); b.dataset.v = o.value;
    seg.appendChild(b); return b; });
  const sync = () => btns.forEach(b => { const on = b.dataset.v === sel.value;
    b.setAttribute("aria-checked", on); b.tabIndex = on ? 0 : -1; });
  const pick = b => { sel.value = b.dataset.v; sync(); sel.dispatchEvent(new Event("change")); };
  btns.forEach((b, i) => {
    b.addEventListener("click", () => pick(b));
    b.addEventListener("keydown", e => {
      const d = {ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1}[e.key];
      if (d) { e.preventDefault(); const n = btns[(i + d + btns.length) % btns.length]; pick(n); n.focus(); }
    });
  });
  sync();
});

/* --- попробуй сам: толщина и ширина (Roboto Flex) --- */
const flex = document.getElementById("flex"), flexNote = document.getElementById("flexNote");
const wght = document.getElementById("wght"), wdth = document.getElementById("wdth"), size = document.getElementById("size");
function updFlex() {
  flex.style.fontVariationSettings = `"wght" ${wght.value}, "wdth" ${wdth.value}`;
  flex.style.fontWeight = wght.value;
  flex.style.fontStretch = wdth.value + "%";
  flex.style.fontSize = size.value + "px";
  document.getElementById("wghtOut").textContent = wght.value;
  document.getElementById("wdthOut").textContent = wdth.value;
  document.getElementById("sizeOut").textContent = size.value;
  const st = D.fonts.stems, lo = st[0], hi = st[st.length - 1];
  flexNote.textContent = `Для сравнения: у шрифтов из датасета (начертание Regular, вес 400) толщина штриха от ${nf(lo)} до ${nf(hi)} кегля, ` +
    `медиана ${nf(st[Math.floor(st.length / 2)])}. При кегле ${size.value} px это от ${(lo * size.value).toFixed(1).replace(".", ",")} до ${(hi * size.value).toFixed(1).replace(".", ",")} px.`;
}
[wght, wdth, size].forEach(el => el.addEventListener("input", updFlex));
document.getElementById("resetPlay").addEventListener("click", () => { wght.value = 400; wdth.value = 100; size.value = 72; updFlex(); });
updFlex();

/* --- попробуй сам: сравнение шрифтов --- */
const GF = D.fonts.pts.filter(p => p.g && p.cap).sort((a, b) => a.f.localeCompare(b.f));
const picks = [...document.querySelectorAll(".fpick")], cmpText = document.getElementById("cmpText"), cmp = document.getElementById("cmp");
const loaded = new Set();
function loadFont(name) {
  if (loaded.has(name)) return Promise.resolve();
  loaded.add(name);
  const l = document.createElement("link");
  l.rel = "stylesheet";
  l.href = "https://fonts.googleapis.com/css2?family=" + name.replace(/ /g, "+") + "&display=swap";
  document.head.appendChild(l);
  return new Promise(res => { l.onload = () => document.fonts.load(`64px "${name}"`).then(res, res); l.onerror = res; setTimeout(res, 4000); });
}
const DEF = ["Inter", "Playfair", "Indie Flower"];
const range = key => { const v = GF.map(p => p[key]).filter(x => x != null).sort((a, b) => a - b);
  return {lo: v[0], hi: v[v.length - 1], med: v[Math.floor(v.length / 2)]}; };
const RG = {x: range("x"), s: range("s"), ct: range("ct"), w: range("w")};
const LAB = {x: "x-height", s: "толщина штриха", ct: "контраст «o»", w: "ширина «o» / x-height"};
picks.forEach((sel, i) => {
  sel.innerHTML = Object.entries(CAT).map(([k, [nm]]) => `<optgroup label="${nm}">` +
    GF.filter(p => p.c === k).map(p => `<option value="${p.f}">${p.f}</option>`).join("") + "</optgroup>").join("");
  const want = GF.find(p => p.f === DEF[i]) || GF[i * 7 % GF.length];
  sel.value = want.f;
  sel.addEventListener("change", renderCmp);
});
cmpText.addEventListener("input", renderCmp);
function bar(p, key) {
  const r = RG[key], v = p[key];
  if (v == null) return `<div class="bar">${LAB[key]}: нет данных</div>`;
  const k = x => Math.max(0, Math.min(1, (x - r.lo) / (r.hi - r.lo))) * 100;
  return `<div class="bar">${LAB[key]}: <b style="color:var(--ink)">${nf(v, key === "ct" ? 2 : 3)}</b>
    <div class="track"><div class="fill" style="width:${k(v)}%;background:${(CAT[p.c] || ["", "#999"])[1]}"></div>
    <div class="med" style="left:${k(r.med)}%" title="медиана датасета"></div></div></div>`;
}
async function renderCmp() {
  const txt = (cmpText.value || "Hxlno").replace(/[<&>"]/g, "");
  const chosen = picks.map(s => GF.find(p => p.f === s.value)).filter(Boolean);
  await Promise.all(chosen.map(p => loadFont(p.f)));
  cmp.innerHTML = chosen.map((p, i) => `<div class="cmp-row"><div class="cmp-head"><b>${p.f}</b>
      <span class="note"><span style="color:#eb6834">- - x-height ${nf(p.x)}</span>&nbsp;&nbsp;
      <span style="color:#1baf7a">- - прописные ${nf(p.cap)}</span>&nbsp;&nbsp;${(CAT[p.c] || [p.c])[0]}</span></div>
      <svg id="cs${i}" viewBox="0 0 640 110" role="img" aria-label="${txt} шрифтом ${p.f}"></svg>
      <div class="bars">${["x", "s", "ct", "w"].map(k => bar(p, k)).join("")}</div></div>`).join("") +
    `<p class="note">Чёрная риска на полоске — медиана по всем шрифтам датасета.</p>`;
  // кегль подбирается по реальной ширине набранного текста: строка всегда помещается
  chosen.forEach((p, i) => {
    const svg = document.getElementById("cs" + i);
    const t = el("text", {x: 8, y: 0, "font-family": `'${p.f}', serif`, "font-size": 72, fill: "#1a1d24"});
    t.textContent = txt; svg.append(t);
    const w72 = t.getComputedTextLength() || 600;
    const FS = Math.max(14, Math.min(72, 72 * 620 / w72)), base = Math.round(FS * Math.max(1, p.cap) + 14), H = base + 16;
    svg.setAttribute("viewBox", `0 0 640 ${H}`);
    t.setAttribute("font-size", FS.toFixed(1)); t.setAttribute("y", base);
    [[base, "#5c6170", null], [base - p.x * FS, "#eb6834", "5 4"], [base - p.cap * FS, "#1baf7a", "5 4"]].forEach(([y, c, d]) => {
      const ln = el("line", {x1: 0, x2: 640, y1: y, y2: y, stroke: c}); if (d) ln.setAttribute("stroke-dasharray", d); svg.insertBefore(ln, t); });
  });
}
renderCmp();

/* --- как читать ρ: облако с заданной силой связи и наши шрифты в рангах --- */
const rhoIn = document.getElementById("rho"), rhoOut = document.getElementById("rhoOut");
const ranks = a => { const idx = a.map((v, i) => [v, i]).sort((p, q) => p[0] - q[0]); const r = new Array(a.length);
  idx.forEach(([, i], k) => r[i] = k); return r; };
const spear = (a, b) => { const ra = ranks(a), rb = ranks(b), n = a.length, m = (n - 1) / 2;
  let sab = 0, saa = 0, sbb = 0; for (let i = 0; i < n; i++) { const x = ra[i] - m, y = rb[i] - m; sab += x * y; saa += x * x; sbb += y * y; }
  return sab / Math.sqrt(saa * sbb); };
let seedZ = 7; const rnd = () => (seedZ = (seedZ * 16807) % 2147483647) / 2147483647;   // фиксированный датчик: облако не прыгает
const Z1 = [], Z2 = [];
for (let i = 0; i < 50; i++) { const u1 = rnd(), u2 = rnd(), r = Math.sqrt(-2 * Math.log(u1));
  Z1.push(r * Math.cos(2 * Math.PI * u2), r * Math.sin(2 * Math.PI * u2)); const v1 = rnd(), v2 = rnd(), q = Math.sqrt(-2 * Math.log(v1));
  Z2.push(q * Math.cos(2 * Math.PI * v2), q * Math.sin(2 * Math.PI * v2)); }
function dots(svg, xs, ys, color) {
  svg.replaceChildren();
  const n = xs.length, X = v => 20 + v / (n - 1) * 260, Y = v => 220 - v / (n - 1) * 200;
  svg.append(el("rect", {x: 14, y: 14, width: 272, height: 212, fill: "none", stroke: "#e6e5e0"}));
  const rx = ranks(xs), ry = ranks(ys);
  for (let i = 0; i < n; i++) svg.append(el("circle", {cx: X(rx[i]), cy: Y(ry[i]), r: 3.4, fill: color, "fill-opacity": .8}));
  const lx = el("text", {x: 150, y: 238, "text-anchor": "middle", "font-size": 11, fill: "#5c6170"}); lx.textContent = "x-height →"; svg.append(lx);
  const ly = el("text", {x: 9, y: 120, "text-anchor": "middle", "font-size": 11, fill: "#5c6170", transform: "rotate(-90 9 120)"}); ly.textContent = "толщина штриха →"; svg.append(ly);
}
function updRho() {
  const r = +rhoIn.value; rhoOut.textContent = nf(r, 2);
  const ys = Z1.map((z, i) => r * z + Math.sqrt(1 - r * r) * Z2[i]);
  dots(document.getElementById("rhoSim"), Z1, ys, "#9aa0a8");
  document.getElementById("rhoSimNote").textContent = `Случайные точки: ρ Спирмена получилось ${nf(spear(Z1, ys), 2)}.`;
  document.querySelectorAll("#rhoPresets button").forEach(b => b.setAttribute("aria-pressed", Math.abs(+b.dataset.v - r) < 1e-9));
}
rhoIn.addEventListener("input", updRho);
document.querySelectorAll("#rhoPresets button").forEach(b => b.addEventListener("click", () => { rhoIn.value = b.dataset.v; updRho(); }));
updRho();
dots(document.getElementById("rhoReal"), D.fonts.pts.map(p => p.x), D.fonts.pts.map(p => p.s), "#2a78d6");

/* --- точечный график шрифтов: приближение и сдвиг --- */
const sc = document.getElementById("scatter"), tip = document.getElementById("tip");
const P = D.fonts.pts, SW = 640, SH = 380;
const FULL = {x: [Math.min(...P.map(p => p.x)) - .01, Math.max(...P.map(p => p.x)) + .01],
              y: [0, Math.max(...P.map(p => p.s)) * 1.08]};
let V = {x: [...FULL.x], y: [...FULL.y]};
const X = v => pad.l + (v - V.x[0]) / (V.x[1] - V.x[0]) * (SW - pad.l - pad.r);
const Y = v => SH - pad.b - (v - V.y[0]) / (V.y[1] - V.y[0]) * (SH - pad.t - pad.b);
const invX = px => V.x[0] + (px - pad.l) / (SW - pad.l - pad.r) * (V.x[1] - V.x[0]);
const invY = py => V.y[0] + (SH - pad.b - py) / (SH - pad.t - pad.b) * (V.y[1] - V.y[0]);
function niceTicks(a, b, n = 5) {               // «круглые» деления: шаг 1, 2 или 5 × 10^k
  const raw = (b - a) / n, p = 10 ** Math.floor(Math.log10(raw)), m = raw / p;
  const st = (m < 1.5 ? 1 : m < 3.5 ? 2 : m < 7.5 ? 5 : 10) * p, out = [];
  for (let t = Math.ceil(a / st) * st; t <= b + 1e-12; t += st) out.push(+t.toFixed(10));
  return [out, Math.max(0, -Math.floor(Math.log10(st) + 1e-9))];
}
const zoomK = () => (FULL.x[1] - FULL.x[0]) / (V.x[1] - V.x[0]);
function clampView() {                          // не уводим график за пределы данных
  ["x", "y"].forEach(a => { const w = Math.min(V[a][1] - V[a][0], FULL[a][1] - FULL[a][0]);
    let lo = Math.max(FULL[a][0], Math.min(V[a][0], FULL[a][1] - w)); V[a] = [lo, lo + w]; });
}
function zoomAt(f, px = (pad.l + SW - pad.r) / 2, py = (pad.t + SH - pad.b) / 2) {
  const cx = invX(px), cy = invY(py), minW = (FULL.x[1] - FULL.x[0]) / 40, minH = (FULL.y[1] - FULL.y[0]) / 40;
  const w = Math.max(minW, (V.x[1] - V.x[0]) / f), h = Math.max(minH, (V.y[1] - V.y[0]) / f);
  const fx = (cx - V.x[0]) / (V.x[1] - V.x[0]), fy = (cy - V.y[0]) / (V.y[1] - V.y[0]);
  V = {x: [cx - fx * w, cx - fx * w + w], y: [cy - fy * h, cy - fy * h + h]}; clampView(); drawScatter();
}
function drawScatter() {
  sc.replaceChildren(); tip.style.opacity = 0;
  const [xt, xd] = niceTicks(V.x[0], V.x[1]), [yt, yd] = niceTicks(V.y[0], V.y[1]);
  axes(sc, xt.filter(t => t > V.x[0] && t < V.x[1]), yt.filter(t => t >= V.y[0] && t < V.y[1]),
       "x-height, доли кегля", "толщина штриха, доли кегля", X, Y, SW, SH, Math.max(2, xd), Math.max(2, yd));
  const defs = document.createElementNS(NS, "defs"), cp = document.createElementNS(NS, "clipPath");
  cp.id = "scClip"; cp.append(el("rect", {x: pad.l, y: pad.t, width: SW - pad.l - pad.r, height: SH - pad.t - pad.b}));
  defs.append(cp); sc.append(defs);
  const g = document.createElementNS(NS, "g"); g.setAttribute("clip-path", "url(#scClip)"); sc.append(g);
  const k = zoomK(), r = Math.min(10, 6 * Math.sqrt(Math.sqrt(k)));
  const vis = P.filter(p => p.x >= V.x[0] && p.x <= V.x[1] && p.s >= V.y[0] && p.s <= V.y[1]);
  vis.forEach(p => {
    const c = el("circle", {cx: X(p.x), cy: Y(p.s), r, fill: (CAT[p.c] || ["", "#999"])[1], "fill-opacity": .85,
      stroke: "#fff", "stroke-width": 1.2, tabindex: 0, "aria-label": `${p.f}: x-height ${nf(p.x)}, штрих ${nf(p.s)}`});
    const show = () => { tip.textContent = `${p.f}: x-height ${nf(p.x)}, штрих ${nf(p.s)}`;
      const b = sc.getBoundingClientRect(), kk = b.width / SW;
      tip.style.left = `${X(p.x) * kk + 12}px`; tip.style.top = `${Y(p.s) * kk - 10}px`; tip.style.opacity = 1; };
    const hide = () => { tip.style.opacity = 0; };
    c.addEventListener("mouseenter", show); c.addEventListener("focus", show);
    c.addEventListener("mouseleave", hide); c.addEventListener("blur", hide);
    g.append(c);
  });
  const boxes = [];                                         // приблизили — подписываем шрифты, без наложений
  if (k > 1.5 && vis.length <= 30) [...vis].sort((a, b) => b.s - a.s).forEach(p => {
    const t = el("text", {x: X(p.x) + r + 3, y: Y(p.s) + 4, "font-size": 11, fill: "#1a1d24", "pointer-events": "none",
      stroke: "#fff", "stroke-width": 3, "paint-order": "stroke"}); t.textContent = p.f; g.append(t);
    const bb = t.getBBox(), hit = boxes.some(o => bb.x < o.x + o.width + 2 && o.x < bb.x + bb.width + 2 && bb.y < o.y + o.height && o.y < bb.y + bb.height);
    if (hit || bb.x + bb.width > SW - pad.r) t.remove(); else boxes.push(bb); });
  document.getElementById("zoomInfo").textContent = k > 1.02
    ? `×${nf(k, 1)} · видно точек: ${vis.length} из ${P.length}` : `весь график · ${P.length} точек`;
  sc.style.cursor = k > 1.02 ? "grab" : "zoom-in";
  sc.style.touchAction = k > 1.02 ? "none" : "pan-y";
}
/* мышь: Ctrl/⌘ + колесо, двойной щелчок; перетаскивание; два пальца — щипок */
const svgPt = e => { const b = sc.getBoundingClientRect(); return [(e.clientX - b.left) * SW / b.width, (e.clientY - b.top) * SW / b.width]; };
const hint = document.getElementById("zoomHint"); let hintT;
sc.addEventListener("wheel", e => {
  if (!(e.ctrlKey || e.metaKey)) { hint.style.opacity = 1; clearTimeout(hintT); hintT = setTimeout(() => hint.style.opacity = 0, 1200); return; }
  e.preventDefault(); const [x, y] = svgPt(e); zoomAt(Math.exp(-e.deltaY * 0.002), x, y);
}, {passive: false});
sc.addEventListener("dblclick", e => { const [x, y] = svgPt(e); zoomAt(e.shiftKey ? 1 / 2 : 2, x, y); });
const ptrs = new Map(); let pinch0 = null;
sc.addEventListener("pointerdown", e => { ptrs.set(e.pointerId, svgPt(e));
  if (ptrs.size === 2) { const [a, b] = [...ptrs.values()]; pinch0 = Math.hypot(a[0] - b[0], a[1] - b[1]); }
  if (zoomK() > 1.02 || ptrs.size === 2) { sc.setPointerCapture(e.pointerId); sc.style.cursor = "grabbing"; } });
sc.addEventListener("pointermove", e => {
  if (!ptrs.has(e.pointerId)) return; const prev = ptrs.get(e.pointerId), cur = svgPt(e); ptrs.set(e.pointerId, cur);
  if (ptrs.size === 2 && pinch0) { const [a, b] = [...ptrs.values()], d = Math.hypot(a[0] - b[0], a[1] - b[1]);
    zoomAt(d / pinch0, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2); pinch0 = d; return; }
  if (zoomK() <= 1.02) return;
  const dx = invX(prev[0]) - invX(cur[0]), dy = invY(prev[1]) - invY(cur[1]);
  V.x = V.x.map(v => v + dx); V.y = V.y.map(v => v + dy); clampView(); drawScatter();
});
const up = e => { ptrs.delete(e.pointerId); if (ptrs.size < 2) pinch0 = null; sc.style.cursor = zoomK() > 1.02 ? "grab" : "zoom-in"; };
sc.addEventListener("pointerup", up); sc.addEventListener("pointercancel", up);
const med = a => { const b = [...a].sort((u, v) => u - v); return b[b.length >> 1]; };
const MX = med(P.map(p => p.x)), MY = med(P.map(p => p.s));   // с полного вида приближаем к «гуще» точек
document.getElementById("zIn").addEventListener("click", () => zoomK() > 1.02 ? zoomAt(1.6) : zoomAt(1.6, X(MX), Y(MY)));
document.getElementById("zOut").addEventListener("click", () => zoomAt(1 / 1.6));
document.getElementById("zReset").addEventListener("click", () => { V = {x: [...FULL.x], y: [...FULL.y]}; drawScatter(); });
drawScatter();
const present = [...new Set(P.map(p => p.c))];
document.getElementById("flegend").innerHTML = Object.entries(CAT).filter(([k]) => present.includes(k))
  .map(([k, [name, col]]) => `<span><i class="sw" style="background:${col}"></i>${name} (${P.filter(p => p.c === k).length})</span>`).join("");
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
