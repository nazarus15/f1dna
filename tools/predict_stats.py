"""Цифри для посту «Підсумки F1 Predict після Гран-прі …».

Запуск:  python3 tools/predict_stats.py [етап]      (без аргументу — останній етап у даних)
Джерело: tools/predict.json (збирає collect_predict.js). Виводить JSON, з якого пишеться пост
за структурою з tools/F1DNA_project_guide.md, розділ 4.
"""
import json, os, re, statistics as S, sys

H = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(H, 'predict.json'), encoding='utf-8'))
lb = d['lb']
rounds = sorted(int(r) for r in lb)
R = int(sys.argv[1]) if len(sys.argv) > 1 else rounds[-1]
if R not in rounds:
    sys.exit(json.dumps({'error': f'немає даних за етап {R}', 'last': rounds[-1]}, ensure_ascii=False))

ADMINS = {'PredictorNaz': 'Назар', 'Lucky Cosmonaut': 'Ді', 'Yaroslav': 'Берт', 'Valeriia': 'Валерія'}
gp = {int(r): re.sub(r'.*\d{4} (.*?) Grand Prix.*', r'\1', q[0]['t']) for r, q in d['qs'].items() if r != '25' and q}

name, played_rows = {}, {}
for r in rounds:
    for x in lb[str(r)]:
        name[x['id']] = (x['n'].strip(), (x['u'] or '').strip())


def played(x):
    return x['p'] is not None and x['acc'] not in (None, '')


cum, acc_hist = {}, {}  # накопичені очки та точність за зіграні етапи на кінець кожного етапу
snap = {}
for r in rounds:
    for x in lb[str(r)]:
        cum[x['id']] = cum.get(x['id'], 0) + (x['p'] or 0)
        if played(x):
            acc_hist.setdefault(x['id'], []).append(int(x['acc']))
    snap[r] = (dict(cum), {k: list(v) for k, v in acc_hist.items()})


def table(r):
    pts, _ = snap[r]
    t = sorted(pts.items(), key=lambda kv: -kv[1])
    rank = {k: 1 + sum(1 for _, w in t if w > v) for k, v in t}
    return t, rank


def acc_leader(r):
    _, ah = snap[r]
    need = 0.6 * r  # щоб не лідирувала команда з 2–3 вдалими етапами
    c = [(round(S.mean(v), 1), k) for k, v in ah.items() if len(v) >= need]
    c.sort(reverse=True)
    top = c[0][0]
    return [{'team': name[k][0], 'owner': name[k][1], 'acc_exact': a, 'acc': round(a), 'total': snap[r][0][k]}
            for a, k in c if a == top]


def overall_acc(k, r):
    v = snap[r][1].get(k, [])
    return round(S.mean(v)) if v else None


cur = [x for x in lb[str(R)] if played(x)]
mx = max(x['p'] for x in cur)
ma = max(int(x['acc']) for x in cur)
t, rk = table(R)
tp, rkp = table(R - 1) if R - 1 in snap else (t, rk)


def team(k, r=R):
    return {'team': name[k][0], 'owner': name[k][1], 'total': snap[r][0][k]}


leaders = [k for k, v in t if v == t[0][1]]
prev_leaders = [k for k, v in tp if v == tp[0][1]]

out = {'round': R, 'gp': gp.get(R), 'next_gp_in_data': gp.get(R + 1),
       'winners': [{'team': x['n'].strip(), 'owner': x['u'].strip(), 'points': x['p'], 'acc': int(x['acc'])} for x in cur if x['p'] == mx],
       'max_acc': {'acc': ma, 'teams': [{'team': x['n'].strip(), 'owner': x['u'].strip()} for x in cur if int(x['acc']) == ma]},
       'leader': [dict(team(k), acc=overall_acc(k, R), prev_rank=rkp[k]) for k in leaders],
       'leader_kept': set(leaders) == set(prev_leaders),
       'prev_leader': [team(k, R - 1) for k in prev_leaders] if R - 1 in snap else None,
       'acc_leader': acc_leader(R), 'prev_acc_leader': acc_leader(R - 1) if R - 1 in snap else None,
       'gaps': {'now': {'1-2': t[0][1] - t[1][1], '1-3': t[0][1] - t[2][1], '1-10': t[0][1] - t[9][1]},
                'prev': {'1-2': tp[0][1] - tp[1][1], '1-3': tp[0][1] - tp[2][1], '1-10': tp[0][1] - tp[9][1]}},
       'top10': [dict(team(k), rank=rk[k], prev_rank=rkp[k]) for k, _ in t[:10]],
       'admins': []}

for k, (n, u) in name.items():
    if n in ADMINS:
        row = next(x for x in lb[str(R)] if x['id'] == k)
        out['admins'].append({'admin': ADMINS[n], 'team': n, 'rank': rk[k], 'prev_rank': rkp[k],
                              'arrow': '➖' if rk[k] == rkp[k] else ('↗️' if rk[k] < rkp[k] else '↘️'),
                              'total': snap[R][0][k], 'acc': overall_acc(k, R),
                              'round_points': row['p'], 'rounds_played': len(snap[R][1].get(k, []))})
out['admins'].sort(key=lambda a: a['rank'])

# Вибір етапу: правильні відповіді і базова вартість (очки за вгадану відповідь, без бустерів)
qs = []
for q in d['qs'][str(R)]:
    o = {x[0]: x for x in q['o']}
    ans = sorted(q['a'], key=lambda a: a[1] or 0)
    qs.append({'no': q['no'], 'q': q['t'], 'options': [x[1] for x in q['o']],
               'answer': [o[a[0]][1] for a in ans if a[0] in o], 'value': [o[a[0]][2] for a in ans if a[0] in o]})
out['questions'] = qs

# Ліга проти світу
avg = lambda r: round(S.mean(x['p'] for x in lb[str(r)] if played(x)), 1)
st = d.get('st', {}).get(str(R)) or []
gl = d.get('gl') or {}
out['league_vs_world'] = {
    'league_avg_points': avg(R), 'league_avg_acc': round(S.mean(int(x['acc']) for x in cur), 1),
    'world_avg_points': gl.get('avgp') if gl.get('gd') == R else None,
    'world_avg_acc': gl.get('avgacc') if gl.get('gd') == R else None,
    'world_share_ge_winner_acc_pct': sum(st[ma // 10 - 1:]) if st and ma >= 10 else None,
    'world_distribution_1_to_10': st, 'played': len(cur), 'teams': len(lb[str(R)]),
    'league_avg_is_season_best': avg(R) == max(avg(r) for r in rounds if r <= R),
    'played_is_season_best': len(cur) == max(sum(1 for x in lb[str(r)] if played(x)) for r in rounds if r <= R)}

# Рекорди сезону станом на етап R і на R-1 (щоб бачити, що змінилось)
def records(upto):
    rs = [r for r in rounds if r <= upto]
    scores = sorted(((x['p'], r, x['n'].strip()) for r in rs for x in lb[str(r)] if played(x)), reverse=True)
    wins, lead = {}, {}
    for r in rs:
        m = max(x['p'] for x in lb[str(r)] if played(x))
        for x in lb[str(r)]:
            if played(x) and x['p'] == m:
                wins.setdefault(x['n'].strip(), []).append(r)
        tt, _ = table(r)
        for k, v in tt:
            if v == tt[0][1]:
                lead.setdefault(name[k][0], []).append(r)
    acc80 = [(int(x['acc']), r, x['n'].strip()) for r in rs for x in lb[str(r)] if played(x) and int(x['acc']) >= 80]
    return {'best_round_score': [{'points': p, 'gp': gp[r], 'team': n} for p, r, n in scores[:5]],
            'most_stage_wins': sorted(({'team': k, 'wins': len(v), 'gps': [gp[r] for r in v]} for k, v in wins.items()), key=lambda z: -z['wins'])[:5],
            'most_rounds_leading': sorted(({'team': k, 'rounds': len(v)} for k, v in lead.items()), key=lambda z: -z['rounds'])[:3],
            'acc_80_plus': [{'acc': a, 'gp': gp[r], 'team': n} for a, r, n in acc80]}

out['records'] = records(R)
out['records_prev'] = records(R - 1) if R - 1 in snap else None
out['winner_score_place_in_season'] = 1 + sum(1 for r in rounds if r <= R for x in lb[str(r)] if played(x) and x['p'] > mx)
out['winner_previous_stage_wins'] = [gp[r] for r in rounds if r < R and any(
    played(x) and x['p'] == max(y['p'] for y in lb[str(r)] if played(y)) and x['n'].strip() in [w['team'] for w in out['winners']]
    for x in lb[str(r)])]
print(json.dumps(out, ensure_ascii=False, indent=1))
