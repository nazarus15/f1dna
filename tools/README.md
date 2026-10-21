# Інструменти сайту

## Автоматичне оновлення

Покрокова інструкція ручного запуску: [UPDATE.md](UPDATE.md).

- `updater.js` — скрипт оновлення. Запускається на сторінці **fantasy.formula1.com** або **f1predict.formula1.com** під залогіненим учасником ліги. Перевіряє, чи з'явилися нові результати, дозбирає лише нові етапи (≤ 1 запит / 0,75 с) і комітить дані в `tools/` через GitHub API.
- Токен GitHub (fine-grained, тільки репозиторій `nazarus15/f1dna`, дозвіл **Contents: Read and write**) вводиться один раз у панелі скрипта і зберігається лише в localStorage цього сайту в цьому браузері.
- `.github/workflows/build.yml` — після коміту даних збирає `index.html` (`build.py`) і комітить його; GitHub Pages публікує сайт.
- Закладка (bookmarklet) для ручного запуску — створити закладку з такою адресою і натиснути її на сторінці ліги:
  ```
  javascript:fetch('https://raw.githubusercontent.com/nazarus15/f1dna/main/tools/updater.js?t='+Date.now()).then(r=>r.text()).then(c=>(0,eval)(c))
  ```
- Статуси (`window.__F1DNA_UPD.status`): `updated`, `up-to-date`, `source-pending` (F1 ще не опублікував результати), `need-token`, `need-login`, `error`.
- На сайті з'являється плашка **Pending**, якщо етап завершився понад 3 години тому, а його результатів ще немає в даних.

## Файли
- `raw_teams.json`, `drivers.json`, `sched.json` — дані F1 Fantasy; `predict.json` — дані F1 Predict.
- `build.py` + `template.html` → `index.html` (та `data.json`), друкує перевірки.
- `collect.js`, `collect_predict.js` — повний збір сезону з нуля (запасний варіант).
- `stats.py` — статистика для постів; `F1DNA_project_guide.md` — формат постів.
