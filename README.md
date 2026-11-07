# Lab01 · КТвД: шрифты, интерактивный датчик, сайт

Быкова Кристина Денисовна (ИСУ 501322), группа 27, трек «Компьютерные технологии в дизайне».
Прикладная статистика, осень 2026. Доп. задание КТвД к лабораторной работе 01.

Основная часть лабораторной (исследование белых вин, трек «Инфохимия», Нефедьева Антонина Сергеевна)
лежит в общем репозитории команды. Отсюда используются её данные Wine Quality (для датчика) и её
пакет `labstat` (статистика и стиль графиков), чтобы обе части выглядели и считались одинаково.

**Сайт:** https://kkristinabbykova.github.io/lab01-ktvd/  
**Репозиторий:** https://github.com/kkristinabbykova/lab01-ktvd

## Что здесь

| Файл | Что это |
|---|---|
| [`fonts.ipynb`](fonts.ipynb) | доп. задание: собственный датасет шрифтов, две случайные величины (x-height и толщина штриха), EDA, (не)зависимость, гипотеза |
| [`datchik.py`](datchik.py) | интерактивный датчик случайных чисел на **marimo**: 3 величины вина, 6 методов, 4 базовых датчика, сравнение с данными |
| `docs/index.html` | лендинг сайта: живой датчик pH, график шрифтов (собирается `tools/build_landing.py`) |
| `labfont/` | измерение пропорций шрифтов по контурам букв (fontTools), схема измерений |
| `labrng/` | датчики: PCG64, вихрь Мерсенна, ЛКГ, RANDU; квантильный, обратная функция, Бокс–Мюллер, полярный, отношений, Неймана |
| `labstat/` | статистика из основной части (автор Нефедьева А. С.) |
| `tests/` | автотесты: датчики, измеритель шрифтов, сборка сайта |
| `data/` | `fonts.csv` (измерения 106 семейств, 100 в анализе — по 20 в каждой категории), `font_categories.csv` (категория и источник: выбор автора или случайный отбор), образец шрифта для схемы, `winequality-white.csv` |
| `tools/` | сборка: случайный отбор шрифтов (`sample_google_fonts.py`), ноутбук шрифтов, исполнитель ноутбуков, сайт |
| `.github/workflows/site.yml` | на каждый push: тесты → экспорт marimo → публикация сайта |

## Критерии КТвД

| Критерий | Где |
|---|---|
| Структура, индексы разделов, якорные ссылки | `fonts.ipynb`: нумерация 1 → 1.1, оглавление, «↑ к содержанию» |
| Скрытие кода | код-ячейки свёрнуты, тег `hide-input` для HTML-экспорта |
| Масштабы, единицы, единый стиль графиков | все графики в стиле `labstat.plots`, единицы на осях, подписи «Рис. N» |
| Формулы в LaTeX | весь текст ноутбуков |
| Доп. задание: датасет, 2 величины, случайность, (не)зависимость, EDA | `fonts.ipynb`, разделы 1–4 |
| Интерактивность для генератора, marimo | `datchik.py`, сайт |
| Доп. баллы: автотесты генератора, таблицы метрик, итеративные коммиты, литература | `tests/`, таблицы в ноутбуке и датчике, история git |

**Осталось написать своими словами:** все места `TODO КТвД` в `fonts.ipynb` (природа событий, что видно на
графиках, вывод о зависимости, общий вывод) и источники из библиотек (РГБ, РНБ, ИТМО).

## Запуск у себя

```bash
pip install -r requirements.txt
python -m pytest -q              # автотесты
marimo edit datchik.py           # интерактивный датчик (откроется в браузере)
jupyter notebook fonts.ipynb     # ноутбук (нужен pip install jupyter)
python tools/build_site.py       # собрать сайт в docs/ (с marimo-датчиком в docs/datchik/)
```

## Публикация на GitHub (один раз)

1. Зарегистрируйся на github.com, нажми **New repository**, имя например `lab01-ktvd`,
   **Private**, без README (он уже есть).
2. В папке этого репозитория выполни (подставь свою почту от GitHub и логин):

   ```bash
   git config user.email "ПОЧТА_ОТ_GITHUB"
   git filter-branch -f --env-filter 'export GIT_AUTHOR_EMAIL="ПОЧТА_ОТ_GITHUB"; export GIT_COMMITTER_EMAIL="ПОЧТА_ОТ_GITHUB"' -- --all
   git remote add origin https://github.com/kkristinabbykova/lab01-ktvd.git
   git push -u origin main
   ```

   Вторая строка заменяет временную почту в уже сделанных коммитах на твою, чтобы GitHub показал их как твои.
3. На GitHub: **Settings → Pages → Source: GitHub Actions**.
4. Вкладка **Actions**: через 2–3 минуты сборка станет зелёной, ссылка на сайт появится в Settings → Pages.
   Если сайт приватного репозитория недоступен на бесплатном тарифе, сделай репозиторий публичным
   или покажи преподавателю ноутбуки и `datchik.py` прямо в репозитории.
5. Необязательно: **Settings → Secrets and variables → Actions → Variables**, переменная `LAB_MAIN_URL`
   со ссылкой на общий репозиторий команды: тогда сайт будет на него ссылаться.
6. Когда преподаватель пришлёт приглашение в учебную организацию, репозиторий можно перенести туда:
   Settings → Danger Zone → **Transfer**. История коммитов сохранится.

## Как добавить шрифты

На fonts.google.com добавь шрифты в подборку и нажми «Download all» **один раз** в конце.
Если семейства нет в `data/font_categories.csv`, допиши строку с категорией из каталога. Дальше:

```bash
python tools/unpack_fonts.py ПАПКА_С_ZIP fonts/
python -m labfont.collect fonts/ data/fonts.csv
python tools/build_fonts_nb.py && python tools/run_nb.py fonts.ipynb
python tools/build_site.py
git add -A && git commit -m "Шрифты: +N семейств" && git push
```

## Литература

1. Брингхерст Р. Основы стиля в типографике. М.: Д. Аронов, 2006.
2. Королькова А. Живая типографика. М.: IndexMarket, 2007.
3. Microsoft. OpenType specification (таблицы head, OS/2, hmtx, fvar).
4. Кнут Д. Э. Искусство программирования. Т. 2. Получисленные алгоритмы. 3-е изд. М.: Вильямс (ЛКГ, RANDU, § 3.3.4).
5. Box G. E. P., Muller M. E. A note on the generation of random normal deviates // Ann. Math. Statist. 1958. Vol. 29. P. 610–611.
6. Marsaglia G., Bray T. A. A convenient method for generating normal variables // SIAM Review. 1964. Vol. 6, № 3. P. 260–264.
7. Kinderman A. J., Monahan J. F. Computer generation of random variables using the ratio of uniform deviates // ACM TOMS. 1977. Vol. 3, № 3. P. 257–260.
8. Azzalini A. A class of distributions which includes the normal ones // Scand. J. Statist. 1985. Vol. 12. P. 171–178 (скошенное нормальное).
9. Matsumoto M., Nishimura T. Mersenne Twister // ACM TOMACS. 1998. Vol. 8, № 1. P. 3–30.
10. O'Neill M. E. PCG: A family of simple fast space-efficient statistically good algorithms for random number generation. HMC-CS-2014-0905, 2014.
11. Cortez P. et al. Modeling wine preferences by data mining from physicochemical properties // Decision Support Systems. 2009. Vol. 47, № 4. P. 547–553.
