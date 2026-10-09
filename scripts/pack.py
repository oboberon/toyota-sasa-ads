import json, sys, argparse
# usage: pack.py weekly.json monthly.json UPDATED_ISO out.json [--daily daily.json] [--prev old_data.json] [--daily-out full_daily.json]
#   --daily: day-level rows (from build.py, d_*.json files). May cover only recent days.
#   --prev:  the current data.json; its day rows older than the first day in --daily are kept,
#            so a scheduled run only needs to re-pull the last few weeks of daily data.
ap = argparse.ArgumentParser()
ap.add_argument('weekly'); ap.add_argument('monthly'); ap.add_argument('updated'); ap.add_argument('out')
ap.add_argument('--daily'); ap.add_argument('--prev'); ap.add_argument('--daily-out')
a = ap.parse_args()
W = json.load(open(a.weekly)); M = json.load(open(a.monthly))
Dn = json.load(open(a.daily)) if a.daily else []

# rows kept from the previous data.json (older days only)
Dold = []
if a.prev:
    P = json.load(open(a.prev))
    first_new = min((r['day'] for r in Dn), default='9999')
    def pname(c):
        return c[2][1:] if c[2].startswith('\u0000') else P['pre'][c[0]] + 'Sale ' + P['sales'][c[1]] + c[2]
    for r in P.get('d', []):
        day = P['days'][r[0]]
        if day >= first_new: continue
        c = P['camps'][r[1]]
        if len(c) < 4: continue  # old format without campaign ids: cannot merge safely
        Dold.append({'day': day, 'campaign': pname(c), 'sale': P['sales'][c[1]], 'campaign_id': c[3],
                     'spend': r[2], 'reach': r[3], 'impressions': r[4], 'clicks': r[5], 'link_clicks': r[6], 'inbox': r[7]})
    print('kept', len(Dold), 'old day rows before', first_new)
cur = {r['campaign_id']: (r['campaign'], r['sale']) for r in W + M + Dn}  # current names win if a campaign was renamed
for r in Dold:
    if r['campaign_id'] in cur: r['campaign'], r['sale'] = cur[r['campaign_id']]
D = sorted(Dold + Dn, key=lambda r: (r['day'], r['sale'], r['campaign']))
if a.daily_out:  # full merged day rows (same shape as build.py output), e.g. for the Claude artifact
    json.dump(D, open(a.daily_out, 'w'), ensure_ascii=False, separators=(',', ':'))

sales, si, pre, pi, camps, ci = [], {}, [], {}, [], {}
def idx(lst, d, v):
    if v not in d: d[v] = len(lst); lst.append(v)
    return d[v]
for r in W + M + D:
    if r['campaign_id'] in ci: continue
    n, s = r['campaign'], r['sale']
    k = n.find('Sale ')
    p, rest = (n[:k], n[k + 5:]) if k >= 0 else ('', n)
    tail = rest[len(s):] if rest.startswith(s) else None
    camps.append([idx(pre, pi, p), idx(sales, si, s), tail if tail is not None else '\u0000' + n, r['campaign_id']])
    ci[r['campaign_id']] = len(camps) - 1
weeks = sorted({r['week'] for r in W}); months = sorted({r['month'] for r in M}); days = sorted({r['day'] for r in D})
wi = {w: i for i, w in enumerate(weeks)}; mi = {m: i for i, m in enumerate(months)}; di = {d: i for i, d in enumerate(days)}
def row(r, ix, key):
    s = r['spend']; s = int(s) if s == int(s) else s
    return [ix[r[key]], ci[r['campaign_id']], s, r['reach'], r['impressions'], r['clicks'], r['link_clicks'], r['inbox']]
out = {'updated': a.updated, 'weeks': weeks, 'months': months, 'days': days, 'sales': sales, 'pre': pre, 'camps': camps,
       'w': [row(r, wi, 'week') for r in W], 'm': [row(r, mi, 'month') for r in M], 'd': [row(r, di, 'day') for r in D]}
json.dump(out, open(a.out, 'w'), ensure_ascii=False, separators=(',', ':'))
# self-check: expand and compare
def name(c):
    p, s, t = c[:3]
    return t[1:] if t.startswith('\u0000') else pre[p] + 'Sale ' + sales[s] + t
for r in W + M + D:
    c = camps[ci[r['campaign_id']]]
    assert name(c) == r['campaign'] and sales[c[1]] == r['sale'], r['campaign']
if D:  # days must be contiguous-ish and not end before the last week starts
    assert days[-1] >= weeks[-1], ('daily data ends before the last week', days[-1], weeks[-1])
print('ok', len(camps), 'camps', len(out['w']), 'week rows', len(out['m']), 'month rows', len(out['d']), 'day rows',
      'days', days[0] if days else None, '->', days[-1] if days else None)
