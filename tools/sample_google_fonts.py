"""Случайный отбор шрифтов из репозитория Google Fonts (github.com/google/fonts) до 20 в каждой категории.

    git clone --filter=blob:none --no-checkout --depth 1 https://github.com/google/fonts gfonts
    python tools/sample_google_fonts.py gfonts fonts/

Категория берётся из METADATA.pb каждого семейства. Порядок кандидатов внутри категории —
random.Random(2026).shuffle по отсортированному списку, поэтому отбор воспроизводим.
Пропускаются семейства без латиницы, уже имеющиеся в data/font_categories.csv и те,
у которых нет настоящих строчных (капитель, униказ). Отобранные дописываются в CSV.
Шаблоны sparse-checkout экранируются: в именах вариативных шрифтов есть [ ].
"""
import csv
import io
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from labfont.measure import _rank, measure_font  # noqa: E402

CAT = {"SANS_SERIF": "sans", "SERIF": "serif", "DISPLAY": "display", "HANDWRITING": "handwriting", "MONOSPACE": "mono"}
TARGET, SEED = 20, 2026


def esc(s):
    return re.sub(r"([\[\]*?])", r"\\\1", s)


def main(repo, dst):
    repo, dst = Path(repo), Path(dst)
    sp = repo / ".git" / "info" / "sparse-checkout"
    subprocess.run(["git", "-C", str(repo), "sparse-checkout", "init", "--no-cone"], check=True)
    sp.write_text("/ofl/*/METADATA.pb\n/apache/*/METADATA.pb\n/ufl/*/METADATA.pb\n")
    subprocess.run(["git", "-C", str(repo), "read-tree", "-mu", "HEAD"], check=True)
    meta = []
    for p in repo.glob("*/*/METADATA.pb"):
        t = p.read_text(encoding="utf-8")
        name, cat = re.search(r'^name:\s*"([^"]+)"', t, re.M), re.search(r'^category:\s*"([^"]+)"', t, re.M)
        if name and cat and cat.group(1) in CAT and re.search(r'^subsets:\s*"latin"', t, re.M):
            meta.append({"dir": str(p.parent.relative_to(repo)), "name": name.group(1), "cat": CAT[cat.group(1)],
                         "files": re.findall(r'filename:\s*"([^"]+)"', t)})
    csv_path = ROOT / "data" / "font_categories.csv"
    have = {r["family_folder"].replace("_", " ").lower(): r["category"] for r in csv.DictReader(open(csv_path, encoding="utf-8"))}
    # считаются только шрифты, годные для анализа (с настоящими строчными), по уже измеренному data/fonts.csv
    count = {c: 0 for c in CAT.values()}
    fonts_csv = ROOT / "data" / "fonts.csv"
    if fonts_csv.exists():
        for r in csv.DictReader(open(fonts_csv, encoding="utf-8")):
            if r["no_lowercase"] == "False" and r["category"] in count:
                count[r["category"]] += 1
    rng = random.Random(SEED)
    plan = {}
    for c in CAT.values():
        pool = sorted((m for m in meta if m["cat"] == c and m["name"].lower() not in have), key=lambda m: m["dir"])
        rng.shuffle(pool)
        plan[c] = pool[: 2 * TARGET]
    pats = [f"/{esc(m['dir'])}/{esc(f)}" for v in plan.values() for m in v for f in m["files"]]
    sp.write_text(sp.read_text() + "\n".join(pats) + "\n")
    subprocess.run(["git", "-C", str(repo), "read-tree", "-mu", "HEAD"], check=True)
    added = []
    for c, pool in plan.items():
        # цель: TARGET в анализе; уже имеющиеся без строчных не считаются
        for m in pool:
            if count[c] >= TARGET:
                break
            files = [repo / m["dir"] / f for f in m["files"]]
            font = min((TTFont(io.BytesIO(f.read_bytes())) for f in files), key=_rank)
            try:
                if measure_font(font).no_lowercase:
                    continue
            except Exception:  # noqa: BLE001
                continue
            out = dst / c / m["name"].replace(" ", "_")
            out.mkdir(parents=True, exist_ok=True)
            for f in files:
                shutil.copy(f, out / f.name)
            added.append((m["name"].replace(" ", "_"), c))
            count[c] += 1
    with open(csv_path, "a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        for folder, c in added:
            w.writerow([folder, c, f"Google Fonts, случайный отбор (seed {SEED})"])
    print(f"добавлено {len(added)}:", count)


if __name__ == "__main__":
    main(*sys.argv[1:3])
