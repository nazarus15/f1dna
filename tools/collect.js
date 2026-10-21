// Збір даних ліги Formula 1 DNA з F1 Fantasy.
// Запускати в консолі (або через javascript_tool) на сторінці https://fantasy.formula1.com
// під залогіненим акаунтом учасника ліги.
// Темп ~1 запит / 0.7 с: швидше F1 Fantasy блокує на кілька хвилин (HTTP 403).
// Результат: window.__F1DNA = {teams, drivers, sched}; JSON.stringify(window.__F1DNA) → raw для tools/build.py
// Параметри: LEAGUE — id ліги; ROUNDS — останній завершений етап; ONLY — масив етапів для дозбору (або null = всі).

(async () => {
  const LEAGUE = 6296404, ROUNDS = 17, ONLY = null;
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const get = async (u) => {
    for (;;) {
      const r = await fetch(u + (u.includes('?') ? '&' : '?') + 'buster=' + Date.now());
      if (r.status === 403 || r.status === 429) { console.warn('blocked, wait 60s'); await sleep(60000); continue; }
      if (!r.ok) return null;
      const x = await r.json(); await sleep(700);
      return x?.Data?.Value ?? x?.Value ?? null;
    }
  };
  const lb = (await get(`/feeds/leaderboard/privateleague/list_1_${LEAGUE}_0_1.json`)).leaderboard;
  const rounds = ONLY || Array.from({ length: ROUNDS }, (_, i) => i + 1);
  const teams = [];
  for (const [k, t] of lb.entries()) {
    const o = await get(`/services/user/opponentteam/opponentgamedayget/1/${t.user_guid}/${t.team_no}`);
    const r = {};
    for (const m of rounds) {
      const v = await get(`/services/user/opponentteam/opponentgamedayplayerteamget/1/${t.user_guid}/${t.team_no}/${m}/1`);
      const x = v?.userTeam?.[0]; if (!x) continue;
      const ids = (x.playerid || []).map(p => p.id);
      const mg = (x.playerid || []).find(p => p.ismgcaptain)?.id || 0;
      r[m] = [x.gdpoints, x.gdrank, x.ovrank, x.ovpoints, x.teamval, x.teambal, x.maxteambal, x.usersubs, x.subsallowed,
        x.boosterid || 0, x.capplayerid || 0, mg, x.inactive_driver_penality_points || 0, ids.join('.'),
        x.finalfxoldplayerid || 0, x.finalfxnewplayerid || 0, x.iswildcard || 0];
    }
    teams.push({ n: decodeURIComponent(t.team_name), u: t.user_name, g: t.user_guid, no: t.team_no, rk: t.cur_rank, p: t.cur_points, tr: t.trend,
      cur: t.user_team.join('.'),
      o: o ? { md: Object.fromEntries(Object.entries(o.mdDetails || {}).map(([a, b]) => [a, b.pts])), wc: o.wildCardtakengd, ll: o.limitLesstakengd,
        ff: o.finalFixtakengd, x3: o.extraDrstakengd, nn: o.noNigativetakengd, ap: o.isAutopilottakengd, tc: o.teamCount, late: o.islateonboard } : null, r });
    console.log(`${k + 1}/${lb.length} ${t.team_name}`);
  }
  const drivers = {};
  for (let m = 1; m <= ROUNDS + 1; m++) {
    const a = await get(`/feeds/drivers/${m}_en.json`);
    drivers[m] = (a || []).map(p => ({ PlayerId: p.PlayerId, Skill: p.Skill, Value: p.Value, TeamName: p.TeamName, FUllName: p.FUllName,
      DisplayName: p.DisplayName, DriverTLA: p.DriverTLA, GamedayPoints: p.GamedayPoints, IsActive: p.IsActive }));
  }
  const sc = await fetch('/feeds/v2/schedule/raceday_en.json?b=' + Date.now()).then(r => r.json());
  const sched = (sc?.Data?.fixtures || []).map(f => ({ GamedayId: f.GamedayId, MeetingName: f.MeetingName, MeetingLocation: f.MeetingLocation,
    CountryName: f.CountryName, CircuitLocation: f.CircuitLocation, SessionName: f.SessionName, SessionType: f.SessionType,
    SessionStartDateISO8601: f.SessionStartDateISO8601, SessionEndDateISO8601: f.SessionEndDateISO8601 }));
  window.__F1DNA = { teams, drivers, sched };
  console.log('done: window.__F1DNA');
})();
