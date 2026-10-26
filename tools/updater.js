// F1 DNA — автоматичне оновлення даних сайту.
// Запуск: на сторінці https://fantasy.formula1.com або https://f1predict.formula1.com під залогіненим учасником ліги
// (закладкою-bookmarklet або через консоль). Скрипт сам визначає, на якому сайті запущений.
// 1) перевіряє, чи з'явилися нові результати; 2) дозбирає лише нові етапи (≤ 1 запит / 0,75 с);
// 3) комітить дані в tools/ репозиторію nazarus15/f1dna; GitHub Action збирає і публікує сайт.
// Токен GitHub (fine-grained, лише цей репозиторій, Contents: Read and write) зберігається
// тільки в localStorage цього сайту в цьому браузері. Стан: window.__F1DNA_UPD.status
// running | updated | up-to-date | source-pending | need-token | need-login | error
(() => {
  if (window.__F1DNA_UPD && window.__F1DNA_UPD.status === 'running') { console.warn('[F1DNA] уже запущено'); return; }
  const REPO = 'nazarus15/f1dna', BR = 'main', TK = 'f1dna_gh_token', FL = 6296404, PL = 494410;
  const S = window.__F1DNA_UPD = { status: 'running', log: [], started: new Date().toISOString() };
  const sleep = ms => new Promise(r => setTimeout(r, ms));

  // ---------- panel ----------
  let box = document.getElementById('f1dna-upd');
  if (!box) { box = document.createElement('div'); box.id = 'f1dna-upd'; document.body.appendChild(box); }
  box.style.cssText = 'position:fixed;right:16px;bottom:16px;z-index:2147483647;width:340px;max-width:calc(100vw - 32px);background:#141413;color:#f0efec;font:13px/1.45 system-ui,sans-serif;border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,.35);padding:12px 14px';
  box.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px"><b>F1 DNA · оновлення сайту</b><button id="f1dna-x" style="background:none;border:0;color:#aaa;font-size:18px;cursor:pointer">×</button></div><div id="f1dna-log" style="max-height:180px;overflow:auto;color:#c3c2b7"></div><div id="f1dna-form"></div>';
  box.querySelector('#f1dna-x').onclick = () => box.remove();
  const logEl = box.querySelector('#f1dna-log');
  const log = s => { S.log.push(s); console.log('[F1DNA]', s); const p = document.createElement('div'); p.textContent = s; logEl.appendChild(p); logEl.scrollTop = 1e9; };
  const finish = (status, msg, extra) => { Object.assign(S, { status, msg, finished: new Date().toISOString() }, extra || {}); log((status === 'error' ? '✗ ' : '✓ ') + msg); };

  // ---------- GitHub ----------
  const tok = () => { try { return localStorage.getItem(TK) || ''; } catch (e) { return ''; } };
  const gh = async (path, opt = {}) => {
    const r = await fetch('https://api.github.com' + path, { ...opt, headers: { Authorization: 'Bearer ' + tok(), 'X-GitHub-Api-Version': '2022-11-28', Accept: 'application/vnd.github+json', ...(opt.headers || {}) } });
    if (!r.ok) throw new Error(`GitHub ${r.status} ${path}: ${(await r.text()).slice(0, 160)}`);
    return opt.raw ? r.text() : r.json();
  };
  const ghRead = async f => JSON.parse(await gh(`/repos/${REPO}/contents/${f}?ref=${BR}&t=${Date.now()}`, { raw: true, headers: { Accept: 'application/vnd.github.raw' } }));
  const ghCommit = async (files, message) => {
    const ref = await gh(`/repos/${REPO}/git/ref/heads/${BR}`), base = ref.object.sha;
    const bc = await gh(`/repos/${REPO}/git/commits/${base}`);
    const tree = [];
    for (const [path, content] of Object.entries(files)) {
      const b = await gh(`/repos/${REPO}/git/blobs`, { method: 'POST', body: JSON.stringify({ content, encoding: 'utf-8' }) });
      tree.push({ path, mode: '100644', type: 'blob', sha: b.sha });
    }
    const t = await gh(`/repos/${REPO}/git/trees`, { method: 'POST', body: JSON.stringify({ base_tree: bc.tree.sha, tree }) });
    const c = await gh(`/repos/${REPO}/git/commits`, { method: 'POST', body: JSON.stringify({ message, tree: t.sha, parents: [base] }) });
    await gh(`/repos/${REPO}/git/refs/heads/${BR}`, { method: 'PATCH', body: JSON.stringify({ sha: c.sha }) });
    return c.sha;
  };
  const askToken = why => {
    const f = box.querySelector('#f1dna-form');
    f.innerHTML = `<p style="margin:8px 0 6px">${why}</p><p style="margin:0 0 6px;color:#aaa">Fine-grained token: лише репозиторій <b>${REPO}</b>, дозвіл Contents — Read and write. <a href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener" style="color:#9ec5f4">Створити токен ↗</a></p>
      <input id="f1dna-tk" type="password" autocomplete="off" placeholder="github_pat_…" style="width:100%;box-sizing:border-box;padding:7px 8px;border-radius:8px;border:1px solid #444;background:#222;color:#fff">
      <button id="f1dna-save" style="margin-top:8px;width:100%;padding:8px;border-radius:8px;border:0;background:#2a78d6;color:#fff;font-weight:700;cursor:pointer">Зберегти токен і запустити</button>`;
    f.querySelector('#f1dna-save').onclick = () => { const v = f.querySelector('#f1dna-tk').value.trim(); if (!v) return; try { localStorage.setItem(TK, v); } catch (e) {} f.innerHTML = ''; S.status = 'restart'; run(); };
  };

  // ---------- F1 feeds ----------
  const get = async u => {
    for (let k = 0; k < 6; k++) {
      const r = await fetch(u + (u.includes('?') ? '&' : '?') + 'buster=' + Date.now());
      if (r.status === 401) throw Object.assign(new Error('Сесія F1 завершилась — увійдіть у свій акаунт на цьому сайті і запустіть ще раз.'), { login: true });
      if (r.status === 403 || r.status === 429) { log('F1 обмежує запити, пауза 60 с…'); await sleep(60000); continue; }
      await sleep(750); if (!r.ok) return null;
      const x = await r.json(); return x?.Data?.Value ?? x?.Value ?? null;
    }
    throw new Error('F1 блокує запити (403). Спробуйте пізніше.');
  };
  const range = (a, b) => Array.from({ length: Math.max(0, b - a + 1) }, (_, i) => a + i);
  const json = o => JSON.stringify(o);

  // ---------- F1 Fantasy ----------
  async function fantasy() {
    log('F1 Fantasy: читаю таблицю ліги…');
    const lbv = await get(`/feeds/leaderboard/privateleague/list_1_${FL}_0_1.json`);
    const lb = lbv?.leaderboard; if (!lb || !lb.length) return finish('need-login', 'Не вдалося прочитати лігу. Увійдіть у F1 Fantasy і запустіть ще раз.');
    const sc = await fetch('/feeds/v2/schedule/raceday_en.json?b=' + Date.now()).then(r => r.json());
    const fixtures = sc?.Data?.fixtures || [];
    const sched = fixtures.map(f => ({ GamedayId: f.GamedayId, MeetingName: f.MeetingName, MeetingLocation: f.MeetingLocation, CountryName: f.CountryName, CircuitLocation: f.CircuitLocation,
      SessionName: f.SessionName, SessionType: f.SessionType, SessionStartDateISO8601: f.SessionStartDateISO8601, SessionEndDateISO8601: f.SessionEndDateISO8601 }));
    const ended = {}; for (const f of fixtures) { const e = new Date(f.SessionEndDateISO8601 || f.SessionStartDateISO8601).getTime(); ended[f.GamedayId] = Math.max(ended[f.GamedayId] || 0, e); }
    log('Читаю дані з репозиторію…');
    const [oldTeams, oldDrivers] = await Promise.all([ghRead('tools/raw_teams.json'), ghRead('tools/drivers.json')]);
    const key = t => `${t.g || t.user_guid}|${t.no || t.team_no}`;
    const old = Object.fromEntries(oldTeams.map(t => [key(t), t]));
    const storedMax = Math.max(0, ...oldTeams.flatMap(t => Object.keys(t.r || {}).map(Number)));
    // season summaries of all teams (also reveal which rounds already have points)
    // перевірка входу: сервіси команд доступні лише залогіненому учаснику
    if (!(await get(`/services/user/opponentteam/opponentgamedayget/1/${lb[0].user_guid}/${lb[0].team_no}`))) return finish('need-login', 'Не вдалося прочитати команди суперників. Увійдіть у F1 Fantasy і запустіть ще раз.');
    const sums = [];
    for (const [k, t] of lb.entries()) { sums.push(await get(`/services/user/opponentteam/opponentgamedayget/1/${t.user_guid}/${t.team_no}`)); if (k % 20 === 19) log(`Підсумки команд: ${k + 1}/${lb.length}`); }
    const now = Date.now();
    const withPts = new Set(sums.flatMap(o => Object.entries(o?.mdDetails || {}).filter(([, b]) => b && b.pts != null).map(([a]) => +a)));
    if (sums.filter(Boolean).length < lb.length * 0.9) return finish('error', 'F1 не віддав підсумки частини команд — дані не закомічено, спробуйте пізніше.');
    const ROUND = Math.max(0, ...[...withPts].filter(m => ended[m] && ended[m] + 2 * 3600e3 < now));
    if (ROUND < storedMax) return finish('error', `F1 повернув етапи лише до R${ROUND}, а на сайті вже R${storedMax} — дані не закомічено.`);
    const sameTotals = lb.length === oldTeams.length && lb.every(t => old[key(t)] && old[key(t)].p === t.cur_points);
    if (ROUND <= storedMax && sameTotals) {
      const nextDone = Object.keys(ended).map(Number).filter(m => m > storedMax && ended[m] + 2 * 3600e3 < now);
      return finish(nextDone.length ? 'source-pending' : 'up-to-date', nextDone.length ? `F1 Fantasy ще не опублікував результати R${Math.min(...nextDone)}.` : `Дані F1 Fantasy актуальні (R${storedMax}).`);
    }
    const fresh = range(storedMax + 1, ROUND); if (!sameTotals && storedMax >= 1) fresh.unshift(storedMax);
    log(`Дозбираю етапи: ${fresh.map(m => 'R' + m).join(', ') || '—'}`);
    const teams = [];
    for (const [k, t] of lb.entries()) {
      const prev = old[key(t)], o = sums[k], r = { ...(prev?.r || {}) };
      for (const m of prev ? fresh : range(1, ROUND)) {
        const v = await get(`/services/user/opponentteam/opponentgamedayplayerteamget/1/${t.user_guid}/${t.team_no}/${m}/1`);
        const x = v?.userTeam?.[0]; if (!x) continue;
        const ids = (x.playerid || []).map(p => p.id), mg = (x.playerid || []).find(p => p.ismgcaptain)?.id || 0;
        r[m] = [x.gdpoints, x.gdrank, x.ovrank, x.ovpoints, x.teamval, x.teambal, x.maxteambal, x.usersubs, x.subsallowed, x.boosterid || 0, x.capplayerid || 0, mg,
          x.inactive_driver_penality_points || 0, ids.join('.'), x.finalfxoldplayerid || 0, x.finalfxnewplayerid || 0, x.iswildcard || 0];
      }
      teams.push({ n: decodeURIComponent(t.team_name), u: t.user_name, g: t.user_guid, no: t.team_no, rk: t.cur_rank, p: t.cur_points, tr: t.trend, cur: (t.user_team || []).join('.'),
        o: o ? { md: Object.fromEntries(Object.entries(o.mdDetails || {}).map(([a, b]) => [a, b.pts])), wc: o.wildCardtakengd, ll: o.limitLesstakengd, ff: o.finalFixtakengd,
          x3: o.extraDrstakengd, nn: o.noNigativetakengd, ap: o.isAutopilottakengd, tc: o.teamCount, late: o.islateonboard } : (prev?.o || null), r });
      if (k % 20 === 19) log(`Склади команд: ${k + 1}/${lb.length}`);
    }
    const drivers = { ...oldDrivers };
    for (const m of new Set([...fresh, ROUND + 1])) {
      const a = await get(`/feeds/drivers/${m}_en.json`); if (!a) continue;
      drivers[m] = a.map(p => ({ PlayerId: p.PlayerId, Skill: p.Skill, Value: p.Value, TeamName: p.TeamName, FUllName: p.FUllName, DisplayName: p.DisplayName, DriverTLA: p.DriverTLA, GamedayPoints: p.GamedayPoints, IsActive: p.IsActive }));
    }
    const bad = teams.filter(t => t.o && Object.values(t.o.md).reduce((a, b) => a + (b || 0), 0) !== t.p).length;
    if (bad) log(`Увага: у ${bad} команд сума етапів ≠ загальні очки (F1 ще перераховує?)`);
    log('Комічу дані в GitHub…');
    const sha = await ghCommit({ 'tools/raw_teams.json': json(teams), 'tools/drivers.json': json(drivers), 'tools/sched.json': json(sched) }, `Дані F1 Fantasy після R${ROUND}`);
    finish('updated', `F1 Fantasy оновлено до R${ROUND} (коміт ${sha.slice(0, 7)}). Сайт збереться за 1–3 хв.`, { round: ROUND });
  }

  // ---------- F1 Predict ----------
  async function predict() {
    const urls = performance.getEntriesByType('resource').map(e => e.name);
    const g = (urls.map(u => (u.match(/\/services\/user\/(?:gameplay|league)\/([0-9a-f-]{36})\//) || [])[1]).find(Boolean));
    if (!g) return finish('need-login', 'Не знайдено сесію F1 Predict. Увійдіть, відкрийте сторінку ліги і запустіть ще раз.');
    log('F1 Predict: перевіряю останній етап…');
    const gd = await get(`/services/user/gameplay/${g}/1/getusergamedaysv1`);
    const ROUND = gd?.latest_gameday?.gameday_id; if (!ROUND) return finish('need-login', 'F1 Predict не віддав дані. Увійдіть і запустіть ще раз.');
    const stored = await ghRead('tools/predict.json');
    const storedMax = Math.max(0, ...Object.keys(stored.lb).map(Number));
    const slimQ = q => (q?.Questions || []).map(x => ({ id: x.Id, no: x.No, t: x.Text, tpl: x.OptionTemplateId, lim: x.Config?.ChoiceLimit,
      o: (x.Options || []).map(o => [o.Id, o.Value, +o.Points, +o.Chance, +o.Position]), a: (x.Answer || []).map(o => [o.Id, +o.Position]) }));
    const lbOf = async m => ((await get(`/services/user/leaderboard/${g}/1/${PL}/${m}/1/1/500/pvtleagueleaderboard`))?.memRank || [])
      .map(x => ({ id: x.teamId, n: decodeURIComponent(x.teamName), u: x.userName, p: x.ovPoints, rk: x.rank, tp: x.overallPoints, tr: x.overallRank, acc: x.correctPercent, t: x.trend }));
    const last = await lbOf(ROUND);
    const qLast = slimQ(await get(`/feeds/questions/questions_${ROUND}_en.json`));
    if (!qLast.length || qLast.every(q => !q.a.length) || last.every(x => x.p == null)) return finish('source-pending', `F1 Predict ще не опублікував результати R${ROUND}.`);
    const oldIds = new Set(Object.values(stored.lb).flat().map(x => x.id));
    const prevTp = Object.fromEntries((stored.lb[storedMax] || []).map(x => [x.id, x.tp]));
    const newMember = last.some(x => !oldIds.has(x.id));
    if (ROUND <= storedMax && !newMember && last.every(x => prevTp[x.id] === x.tp)) return finish('up-to-date', `Дані F1 Predict актуальні (R${storedMax}).`);
    const lb = { ...stored.lb }, qs = { ...stored.qs }, st = { ...stored.st };
    const rounds = newMember ? range(1, ROUND) : range(Math.min(storedMax, ROUND), ROUND);
    log(`Дозбираю етапи: ${rounds.map(m => 'R' + m).join(', ')}${newMember ? ' (новий учасник — оновлюю весь сезон)' : ''}`);
    for (const m of rounds) {
      lb[m] = m === ROUND ? last : await lbOf(m);
      if (m > storedMax || !qs[m]?.length) qs[m] = m === ROUND ? qLast : slimQ(await get(`/feeds/questions/questions_${m}_en.json`));
      if (m > storedMax || !st[m]?.length) st[m] = ((await get(`/services/user/gameplay/${g}/${m}/1/userStats`)) || []).map(s => s.prct);
    }
    const qb = slimQ(await get(`/feeds/questions/questions_25_en.json`)); if (qb.length) qs[25] = qb;
    const lg = gd.latest_gameday; const gl = { gd: lg.gameday_id, avgp: lg.global_avg_points, avgacc: lg.global_avg_percentage };
    const sum = {}; for (const m of Object.keys(lb)) for (const x of lb[m]) sum[x.id] = (sum[x.id] || 0) + (x.p || 0);
    const bad = last.filter(x => sum[x.id] !== x.tp).length;
    if (bad) return finish('error', `Сума очок не збігається з підсумком у ${bad} учасників — дані не закомічено, спробуйте пізніше.`);
    log('Комічу дані в GitHub…');
    const sha = await ghCommit({ 'tools/predict.json': json({ lb, qs, st, gl }) }, `Дані F1 Predict після R${ROUND}`);
    finish('updated', `F1 Predict оновлено до R${ROUND} (коміт ${sha.slice(0, 7)}). Сайт збереться за 1–3 хв.`, { round: ROUND });
  }

  async function run() {
    S.status = 'running';
    try {
      if (!tok()) { S.status = 'need-token'; S.msg = 'Потрібен токен GitHub'; log('Потрібен токен GitHub (вводиться один раз у цьому браузері).'); return askToken('Вставте токен GitHub:'); }
      try { await gh(`/repos/${REPO}`); } catch (e) { S.status = 'need-token'; S.msg = 'Токен недійсний'; log('Токен GitHub недійсний або без доступу до репозиторію.'); return askToken('Токен не підходить. Вставте новий:'); }
      if (/fantasy\.formula1\.com$/.test(location.hostname)) await fantasy();
      else if (/f1predict\.formula1\.com$/.test(location.hostname)) await predict();
      else finish('error', 'Запускайте на fantasy.formula1.com або f1predict.formula1.com');
    } catch (e) { finish(e.login ? 'need-login' : 'error', String(e.message || e)); }
  }
  run();
})();
