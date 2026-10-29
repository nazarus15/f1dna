#!/usr/bin/env python3
"""Build data.json + index.html for the Formula 1 DNA league site.
Inputs (in this folder): raw_teams.json, drivers.json, sched.json
"""
import json, datetime, sys, os
H = os.path.dirname(os.path.abspath(__file__))
rd = lambda f: json.load(open(os.path.join(H, f), encoding='utf-8'))

teams = rd('raw_teams.json')
drivers = rd('drivers.json')      # {gd: [player,...]}
fixtures = rd('sched.json')       # list of fixtures

ISO = {'Australia':'AU','China':'CN','Japan':'JP','Bahrain':'BH','Saudi Arabia':'SA','USA':'US','United States':'US','Canada':'CA',
 'Monaco':'MC','Spain':'ES','Austria':'AT','Great Britain':'GB','United Kingdom':'GB','Belgium':'BE','Hungary':'HU','Netherlands':'NL',
 'Italy':'IT','Azerbaijan':'AZ','Singapore':'SG','Mexico':'MX','Brazil':'BR','Qatar':'QA','Abu Dhabi':'AE','United Arab Emirates':'AE',
 'Las Vegas':'US','Miami':'US','Malaysia':'MY','Portugal':'PT','Turkey':'TR','France':'FR','Germany':'DE','Russia':'RU','Argentina':'AR','South Africa':'ZA','Thailand':'TH','Korea':'KR'}
SHORT = {'AU':'AUS','CN':'CHN','JP':'JPN','BH':'BHR','SA':'SAU','US':'USA','CA':'CAN','MC':'MON','ES':'ESP','AT':'AUT','GB':'GBR','BE':'BEL',
 'HU':'HUN','NL':'NED','IT':'ITA','AZ':'AZE','SG':'SGP','MX':'MEX','BR':'BRA','QA':'QAT','AE':'ABU','MY':'MAL','PT':'POR','TR':'TUR',
 'FR':'FRA','DE':'GER','RU':'RUS','AR':'ARG','ZA':'RSA','TH':'THA','KR':'KOR'}
flag = lambda iso: ''.join(chr(0x1F1E6 + ord(c) - 65) for c in iso) if iso and len(iso) == 2 else ''
SESS_UA = {'Qualifying':'Кваліфікація','Race':'Гонка','Sprint Qualifying':'Спринт-кв.','Sprint':'Спринт'}

# forward-fill team value / budget on races where no transfers were saved (API returns null)
for t in teams:
    prev = None
    for m in sorted(t.get('r', {}), key=int):
        rr = t['r'][m]
        if rr[4] is None and prev: rr[4] = prev[4]
        if rr[6] is None and prev: rr[6] = prev[6]
        if rr[5] is None and prev: rr[5] = prev[5]
        prev = rr

done_md = set()
for t in teams:
    for m in (t.get('o') or {}).get('md', {}): done_md.add(int(m))
    for m in t.get('r', {}): done_md.add(int(m))

races = {}
for f in fixtures:
    g = int(f['GamedayId'])
    r = races.setdefault(g, {'r': g, 'sessions': []})
    r['name'] = f['MeetingName']; r['loc'] = f.get('MeetingLocation') or f.get('CircuitLocation')
    iso = ISO.get(f.get('CountryName'), ISO.get(f.get('CircuitLocation'), ''))
    r['flag'] = f'<span class="flag">{flag(iso)}</span>' if iso else ''
    r['short'] = {'Miami Grand Prix':'MIA','Las Vegas Grand Prix':'LVG','Barcelona Grand Prix':'BCN'}.get(f['MeetingName']) or SHORT.get(iso, (f.get('CountryName') or '')[:3].upper())
    r['sessions'].append({'n': SESS_UA.get(f['SessionName'], f['SessionName']), 't': f['SessionStartDateISO8601'], 'e': f.get('SessionEndDateISO8601')})
    if 'Sprint' in f['SessionType']: r['sprint'] = True
for r in races.values():
    r['sessions'].sort(key=lambda s: s['t'])
    r['start'] = r['sessions'][0]['t']; r['end'] = r['sessions'][-1]['e'] or r['sessions'][-1]['t']
    r['deadline'] = r['sessions'][0]['t']
    r['done'] = r['r'] in done_md
    for s in r['sessions']: s.pop('e', None)
races = [races[k] for k in sorted(races)]

players = {}
for gd in sorted(drivers, key=int):
    for p in drivers[gd] or []:
        players[str(p['PlayerId'])] = {'t': p.get('DriverTLA') or p['DisplayName'][:3].upper(), 'n': p['FUllName'],
            'team': p.get('TeamName') or '', 'k': int(p['Skill']), 'v': p['Value'], 'a': 0 if str(p.get('IsActive','1'))=='0' else 1}
# price of each player by gameday (value before that gameday)
pval = {}
for gd in sorted(drivers, key=int):
    for p in drivers[gd] or []:
        pval.setdefault(str(p['PlayerId']), {})[gd] = p['Value']
# per-race fantasy points of each player (from that gameday feed)
ppts = {}
for gd, arr in drivers.items():
    if int(gd) in done_md and arr:
        ppts[gd] = {str(p['PlayerId']): float(p.get('GamedayPoints') or 0) for p in arr}

me = [f"{t['g']}|{t['no']}" for t in teams if t['u'].strip().lower() == 'nazarii palii']

# ---- F1 Predict league (optional input predict.json) ----
pred = None
if os.path.exists(os.path.join(H, 'predict.json')):
    pr = rd('predict.json')
    users = {}
    for m, arr in pr['lb'].items():
        for r in arr:
            u = users.setdefault(r['id'], {'id': r['id'], 'n': r['n'].strip(), 'u': r['u'].strip(), 'p': {}, 'a': {}, 'rk': {}})
            if r['p'] is not None:
                u['p'][m] = r['p']; u['a'][m] = int(r['acc']) if r['acc'] not in (None, '') else None; u['rk'][m] = r['rk']
    def slim(q):  # options: [id, name, points, chance, position]
        return {'no': q['no'], 't': q['t'], 'tpl': q['tpl'], 'lim': q['lim'], 'o': [[o[0], o[1], o[2]] for o in q['o']], 'a': q['a']}
    rounds = sorted(int(m) for m in pr['lb'])
    pred = {'league': {'id': 494410, 'name': 'Formula 1 DNA'}, 'rounds': rounds, 'users': list(users.values()),
            'qs': {m: [slim(q) for q in pr['qs'][str(m)]] for m in rounds},
            'bonus': [slim(q) for q in pr['qs'].get('25', [])],
            'world': pr.get('st', {}), 'gl': pr.get('gl')}
    for u in pred['users']:
        s = sum(u['p'].values())
        assert s == next(r['tp'] for r in pr['lb'][str(rounds[-1])] if r['id'] == u['id']), u['n']

def data_time():
    # час останньої зміни даних (git), а не час збірки; запасний варіант — зараз
    import subprocess
    try:
        t = subprocess.run(['git', 'log', '-1', '--format=%cI', '--', 'raw_teams.json', 'predict.json', 'drivers.json'],
                           cwd=H, capture_output=True, text=True, timeout=20).stdout.strip()
        if t: return datetime.datetime.fromisoformat(t).astimezone(datetime.timezone.utc).isoformat(timespec='seconds')
    except Exception: pass
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')

# на публічний сайт — лише короткий числовий id акаунта замість повного guid F1
import copy
teams = copy.deepcopy(teams)
for t in teams:
    t['g'] = str(t['g']).split('-0-')[-1]
me = [f"{t['g']}|{t['no']}" for t in teams if t['u'].strip().lower() == 'nazarii palii']

data = {'league': {'id': 6296404, 'name': 'Formula 1 DNA', 'size': len(teams)}, 'pred': pred,
        'updated': data_time(),
        'races': races, 'players': players, 'ppts': ppts, 'pval': pval, 'teams': teams, 'me': me}
js = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
open(os.path.join(H, 'data.json'), 'w', encoding='utf-8').write(js)
tpl = open(os.path.join(H, 'template.html'), encoding='utf-8').read()
out = tpl.replace('/*__DATA__*/null', js.replace('</', '<\\/'))
# Google Analytics: Measurement ID з tools/ga_id.txt (якщо файлу немає — аналітика вимкнена)
ga_path = os.path.join(H, 'ga_id.txt')
ga_id = open(ga_path).read().strip() if os.path.exists(ga_path) else ''
out = out.replace('/*__GA_ID__*/', ga_id)
# повний HTML-документ для GitHub Pages: doctype (без quirks mode), кодування, viewport, іконки-файли
if not out.lstrip().lower().startswith('<!doctype'):
    out = ('<!doctype html>\n<html lang="uk">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
           '<link rel="icon" type="image/svg+xml" href="favicon.svg">\n'
           '<link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">\n'
           '<link rel="icon" type="image/png" sizes="192x192" href="favicon-192.png">\n'
           '<link rel="apple-touch-icon" href="apple-touch-icon.png">\n'
           '<meta name="description" content="Неофіційна аналітика приватних ліг «Formula 1 DNA» у F1 Fantasy та F1 Predict: таблиці, результати етапів, суперники, рекорди сезону.">\n'
           '<meta name="theme-color" content="#d6202b">\n'
           '<meta property="og:type" content="website">\n'
           '<meta property="og:site_name" content="Formula 1 DNA">\n'
           '<meta property="og:title" content="Formula 1 DNA — аналітика ліг F1 Fantasy і F1 Predict">\n'
           '<meta property="og:description" content="Таблиці, результати етапів, аналітика, суперники й рекорди сезону 2026.">\n'
           '<meta property="og:url" content="https://nazarus15.github.io/f1dna/">\n'
           '<meta property="og:image" content="https://nazarus15.github.io/f1dna/og.png">\n'
           '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">\n'
           '<meta name="twitter:card" content="summary_large_image">\n') + out
open(os.path.join(H, 'index.html'), 'w', encoding='utf-8').write(out)

# sanity report
missing_r = sum(1 for t in teams for m in done_md if str(m) not in t['r'])
missing_o = sum(1 for t in teams if not t.get('o'))
bad = [t['n'] for t in teams if t.get('o') and sum(t['o']['md'].values()) != t['p']]
print(f"teams={len(teams)} races_done={sorted(done_md)} players={len(players)} me={me}")
print(f"missing race records={missing_r} missing season records={missing_o}")
print(f"sum(md)!=total for {len(bad)} teams: {bad[:5]}")
print(f"index.html {len(out)//1024} KB")
