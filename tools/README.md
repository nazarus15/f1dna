# Інструменти сайту і постів

- `collect.js` — збір даних ліги в браузері (залогінений F1 Fantasy). Результат `window.__F1DNA` → зберегти `teams` у `raw_teams.json`, `drivers` у `drivers.json`, `sched` у `sched.json`.
- `build.py` — з `raw_teams.json`, `drivers.json`, `sched.json` і `template.html` будує `index.html` (скопіювати в корінь репозиторію) та `data.json`; друкує перевірки (сума очок = загальні очки).
- `stats.py` — рахує статистику для постів (рубрики з `F1DNA_project_guide.md`). Запуск після `build.py`.
- `F1DNA_project_guide.md` — формат посту, правила мови, рубрики, опис даних.

Оновлення після етапу: `collect.js` (можна лише новий етап через `ONLY=[n]` і злиття з наявним `raw_teams.json`) → `python3 build.py` → `cp index.html ../index.html` → коміт.
