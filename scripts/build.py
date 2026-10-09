import json, glob, re, sys, collections
raw = sys.argv[1]
def rows(prefix):
    out = []
    for f in sorted(glob.glob(f'{raw}/{prefix}_*.json')):
        d = json.load(open(f))
        if d.get('pagination', {}).get('next_cursor'): print('WARN more pages', f, file=sys.stderr)
        out += json.loads(d['ad_entities'])
    return out
NAME = re.compile(r'Sale\s+(.+?)\s*-\s*\W?[A-Za-z]+\s+\d{4}')
def sale(n):
    n = n.replace(chr(0x200b), '')
    m = NAME.search(n)
    s = m.group(1) if m else n.split('Sale', 1)[1]
    return re.sub(r'\s+', ' ', s.replace(chr(0x200b), '')).strip(' -')
def num(x): 
    try: return float(x)
    except: return 0.0
def inbox(r):
    res = r.get('results') or {}
    if 'messaging_conversation_started' not in res.get('indicator', ''): return 0
    v = res.get('values') or []
    return int(num(v[0]['value'])) if v else 0
def shape(r, key):
    return {key: r['date_start'], 'sale': sale(r['name']), 'campaign': r['name'], 'campaign_id': r['id'],
            'spend': round(num(r['amount_spent']['value']), 2), 'reach': int(num(r['reach'])),
            'impressions': int(num(r['impressions'])), 'clicks': int(num(r['clicks'])),
            'link_clicks': int(num(r['link_click'])), 'inbox': inbox(r)}
for prefix, key, out in [('w', 'week', 'weekly.json'), ('m', 'month', 'monthly.json')]:
    R = [shape(r, key) for r in rows(prefix) if num(r['amount_spent']['value']) > 0 or num(r['impressions']) > 0]
    if key == 'month': 
        for r in R: r['month'] = r['month'][:7]
    seen = {}; 
    for r in R: seen[(r[key], r['campaign_id'])] = r   # later files win (refresh)
    R = sorted(seen.values(), key=lambda r: (r[key], r['sale'], r['campaign']))
    json.dump(R, open(f'{raw}/../{out}', 'w'), ensure_ascii=False, separators=(',', ':'))
    print(out, len(R), 'spend', round(sum(r['spend'] for r in R), 2), 'inbox', sum(r['inbox'] for r in R))
    print(collections.Counter(r['sale'] for r in R).most_common())
