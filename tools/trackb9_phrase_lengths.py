"""Verify known term widths before scanning unrelated token bytes."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
old = '''                const uint8_t* t = s;
                while (t < e && LOWER.t[*t]) ++t;
                if (is_term(s, t - s, anchor) && around(b, e, s, t, phrase, j)) return true;'''
new = '''                const size_t len = terms_.length(anchor);
                if (size_t(e - s) < len || !is_term(s, len, anchor)) continue;
                const uint8_t* t = s + len;
                if (t < e && LOWER.t[*t]) continue;
                if (around(b, e, s, t, phrase, j)) return true;'''
back_old = '''            const uint8_t* end = s;
            while (s > b && LOWER.t[s[-1]]) --s;
            if (s == end || !is_term(s, end - s, phrase[i])) return false;'''
back_new = '''            const size_t len = terms_.length(phrase[i]);
            if (size_t(s - b) < len) return false;
            s -= len;
            if ((s > b && LOWER.t[s[-1]]) || !is_term(s, len, phrase[i])) return false;'''
forward_old = '''            const uint8_t* start = t;
            while (t < e && LOWER.t[*t]) ++t;
            if (t == start || !is_term(start, t - start, phrase[i])) return false;'''
forward_new = '''            const size_t len = terms_.length(phrase[i]);
            if (size_t(e - t) < len || !is_term(t, len, phrase[i])) return false;
            t += len;
            if (t < e && LOWER.t[*t]) return false;'''
for label in ['hybrid-owner2', 'query-buffers']:
    source = (PROTO / f'trackb9-{label}.cpp').read_text()
    assert source.count(old) == source.count(back_old) == source.count(forward_old) == 1
    source = source.replace(old, new)
    (PROTO / f'trackb9-anchorlength-{label}.cpp').write_text(source)
    source = source.replace(back_old, back_new).replace(forward_old, forward_new)
    (PROTO / f'trackb9-knownlength-{label}.cpp').write_text(source)
print('Created exact fixed-length anchor and neighbouring-token checks.')
