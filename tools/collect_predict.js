// Збір даних ліги F1 Predict «Formula 1 DNA» (494410).
// Запускати в консолі на https://f1predict.formula1.com під залогіненим учасником ліги.
// Темп ~1 запит / 0.75 с. Результат: window.__PRS (JSON-рядок) → зберегти як tools/predict.json для build.py.
(async () => {
  const L = 494410, ROUNDS = 17, BONUS = 25, sl = ms => new Promise(r => setTimeout(r, ms));
  const g = (performance.getEntriesByType('resource').map(e => e.name).find(u => u.includes('/services/user/gameplay/')) || '').split('/gameplay/')[1]?.split('/')[0];
  if (!g) { console.error('Відкрийте будь-яку сторінку предиктора, щоб отримати guid'); return; }
  const get = async u => { for (let k = 0; k < 5; k++) { const r = await fetch(u + (u.includes('?') ? '&' : '?') + 'buster=' + Date.now());
    if (r.status === 403 || r.status === 429) { await sl(60000); continue; } await sl(750); if (!r.ok) return null; const x = await r.json(); return x?.Data?.Value ?? null; } return null; };
  const slimQ = q => (q?.Questions || []).map(x => ({ id: x.Id, no: x.No, t: x.Text, tpl: x.OptionTemplateId, lim: x.Config?.ChoiceLimit,
    o: (x.Options || []).map(o => [o.Id, o.Value, +o.Points, +o.Chance, +o.Position]), a: (x.Answer || []).map(o => [o.Id, +o.Position]) }));
  const lb = {}, qs = {}, st = {};
  for (let m = 1; m <= ROUNDS; m++) {
    const v = await get(`/services/user/leaderboard/${g}/1/${L}/${m}/1/1/500/pvtleagueleaderboard`);
    lb[m] = (v?.memRank || []).map(x => ({ id: x.teamId, n: decodeURIComponent(x.teamName), u: x.userName, p: x.ovPoints, rk: x.rank, tp: x.overallPoints, tr: x.overallRank, acc: x.correctPercent, t: x.trend }));
    qs[m] = slimQ(await get(`/feeds/questions/questions_${m}_en.json`));
    st[m] = ((await get(`/services/user/gameplay/${g}/${m}/1/userStats`)) || []).map(s => s.prct); // світовий розподіл 1/10..10/10
    console.log('round', m);
  }
  qs[BONUS] = slimQ(await get(`/feeds/questions/questions_${BONUS}_en.json`));
  const gd = await get(`/services/user/gameplay/${g}/1/getusergamedaysv1`);
  const gl = gd?.latest_gameday ? { gd: gd.latest_gameday.gameday_id, avgp: gd.latest_gameday.global_avg_points, avgacc: gd.latest_gameday.global_avg_percentage } : null;
  window.__PRS = JSON.stringify({ lb, qs, st, gl }); console.log('done: window.__PRS', window.__PRS.length);
})();
