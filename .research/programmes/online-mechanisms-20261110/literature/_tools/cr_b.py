import json, urllib.parse, urllib.request, time
UA = 'lit/1.0 (mailto:r@example.org)'


def q(s, rows=5):
    p = {'query.bibliographic': s, 'rows': str(rows),
         'select': 'DOI,title,container-title,issued,author'}
    u = 'https://api.crossref.org/works?' + urllib.parse.urlencode(p)
    r = urllib.request.Request(u, headers={'User-Agent': UA})
    j = json.loads(urllib.request.urlopen(r, timeout=45).read().decode('utf-8'))
    return j['message']['items']


QS = [
    ('holistic', 'A holistic aging model for Li(NiMnCo)O2 based 18650 lithium-ion batteries'),
    ('preger', 'Degradation of Commercial Lithium-Ion Cells as a Function of Chemistry and Cycling Conditions'),
    ('wang2011', 'Cycle-life model for graphite-LiFePO4 cells'),
    ('ecker2014', 'Calendar and cycle life study of Li(NiMnCo)O2-based 18650 lithium-ion batteries'),
    ('dod-exp', 'depth of discharge exponent cycle life model lithium-ion battery empirical'),
    ('efc-fail', 'equivalent full cycle normalization degradation depth of discharge collapse'),
    ('dod2025', 'depth of discharge effect lithium-ion battery lifetime model'),
    ('throughput', 'charge throughput normalization battery degradation operating condition'),
]

for tag, s in QS:
    print('## ' + tag + ' :: ' + s)
    try:
        for it in q(s):
            t = ' '.join(it.get('title') or [''])
            y = ((it.get('issued') or {}).get('date-parts') or [[None]])[0][0]
            ven = ' '.join(it.get('container-title') or [''])[:44]
            print('   %s | %-44s | %-32s | %s' % (y, ven, it.get('DOI'), ' '.join(t.split())[:96]))
    except Exception as e:
        print('   ERR', e)
    time.sleep(0.5)
