import json, sys
# usage: pack.py weekly.json monthly.json updated_iso out.json
W = json.load(open(sys.argv[1])); M = json.load(open(sys.argv[2]))
sales, si, pre, pi, camps, ci = [], {}, [], {}, [], {}
def idx(lst, d, v):
    if v not in d: d[v] = len(lst); lst.append(v)
    return d[v]
for r in W + M:
    if r['campaign_id'] in ci: continue
    n, s = r['campaign'], r['sale']
    k = n.find('Sale ')
    p, rest = (n[:k], n[k + 5:]) if k >= 0 else ('', n)
    tail = rest[len(s):] if rest.startswith(s) else None
    camps.append([idx(pre, pi, p), idx(sales, si, s), tail if tail is not None else '\u0000' + n])
    ci[r['campaign_id']] = len(camps) - 1
weeks = sorted({r['week'] for r in W}); months = sorted({r['month'] for r in M})
wi = {w: i for i, w in enumerate(weeks)}; mi = {m: i for i, m in enumerate(months)}
def row(r, ix, key):
    s = r['spend']; s = int(s) if s == int(s) else s
    return [ix[r[key]], ci[r['campaign_id']], s, r['reach'], r['impressions'], r['clicks'], r['link_clicks'], r['inbox']]
out = {'updated': sys.argv[3], 'weeks': weeks, 'months': months, 'sales': sales, 'pre': pre, 'camps': camps,
       'w': [row(r, wi, 'week') for r in W], 'm': [row(r, mi, 'month') for r in M]}
json.dump(out, open(sys.argv[4], 'w'), ensure_ascii=False, separators=(',', ':'))
# self-check: expand and compare
def name(c):
    p, s, t = c
    return t[1:] if t.startswith('\u0000') else pre[p] + 'Sale ' + sales[s] + t
for r in W + M:
    c = camps[ci[r['campaign_id']]]
    assert name(c) == r['campaign'] and sales[c[1]] == r['sale'], r['campaign']
print('ok', len(camps), 'camps')
