"""Проверки сборки сайта и marimo-ноутбука."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_public_copy_in_sync():
    """В браузере датчик берёт код из public/: копия должна совпадать с labrng (tools/build_site.py)."""
    assert (ROOT / "public" / "generators.py").read_text() == (ROOT / "labrng" / "generators.py").read_text()


def test_landing_has_no_placeholders():
    html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    assert "__" not in html.replace("__proto__", "")
    assert '<html lang="ru">' in html


def test_marimo_notebook_is_valid_python():
    compile((ROOT / "datchik.py").read_text(encoding="utf-8"), "datchik.py", "exec")
