"""Key generation and in-place rewriting of .bib and .tex files."""
import re
import unicodedata

STOPWORDS = set("a an the of on in for and to with from by at as is are via toward towards using "
                "into over under its their our".split())

_ENTRY = re.compile(r"(@(\w+)\s*\{\s*)([^,\s]+)(\s*,)")
# \cite, \citep, \citet*, \autocite, \parencite, \textcite, \nocite ... with optional [..] args
_CITE = re.compile(r"(\\[A-Za-z]*cite[A-Za-z]*\*?(?:\s*\[[^\]]*\]){0,2}\s*\{)([^}]*)(\})")


def _ascii(s):
    s = re.sub(r"\\[a-zA-Z]+\s*|[{}\\'\"`^~]", "", s)
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def _field(body, name):
    m = re.search(r"\b%s\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|\"[^\"]*\"|\w+)" % name, body, re.IGNORECASE)
    if not m:
        return ""
    v = m.group(1)
    return v[1:-1] if v[0] in "{\"" else v


def read_entries(text):
    """Return a list of (key, fields) where fields has author, year, title (raw strings)."""
    out = []
    matches = list(_ENTRY.finditer(text))
    for idx, m in enumerate(matches):
        if m.group(2).lower() in ("comment", "string", "preamble"):
            continue
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[m.end():end]
        out.append((m.group(3), {k: _field(body, k) for k in ("author", "editor", "year", "title")}))
    return out


def _surname(person):
    person = person.strip()
    if "," in person:
        last = person.split(",")[0]
    else:
        parts = person.split()
        last = parts[-1] if parts else ""
        # keep particles such as "van der" attached: "van der Waals" -> "vanderwaals"
        for i, p in enumerate(parts[:-1]):
            if p[:1].islower():
                last = "".join(parts[i:])
                break
    return re.sub(r"[^A-Za-z]", "", _ascii(last))


def make_key(fields, pattern="{author}{year}{word}"):
    """Build a key from fields. Placeholders: {author} first surname, {Author} capitalized,
    {authors2} first two surnames, {etal} surname + 'EtAl' if >2 authors, {year}, {word} first
    non-stopword of the title, {words3} first three title words."""
    names = [a for a in (fields.get("author") or fields.get("editor") or "").split(" and ") if a.strip()]
    surnames = [_surname(a) for a in names] or ["anon"]
    words = [w for w in re.findall(r"[A-Za-z0-9]+", _ascii(fields.get("title", "")).lower()) if w not in STOPWORDS]
    year = re.search(r"\d{4}", fields.get("year", "") or "")
    values = {
        "author": surnames[0].lower(),
        "Author": surnames[0].capitalize(),
        "authors2": "".join(s.capitalize() for s in surnames[:2]),
        "etal": surnames[0].capitalize() + ("EtAl" if len(surnames) > 2 else "".join(s.capitalize() for s in surnames[1:2])),
        "year": year.group(0) if year else "nd",
        "word": words[0] if words else "",
        "words3": "".join(w.capitalize() for w in words[:3]),
    }
    return pattern.format(**values)


def plan_keys(entries, pattern="{author}{year}{word}"):
    """Return an ordered dict old_key -> new_key, adding a/b/c suffixes to disambiguate."""
    base = [(old, make_key(f, pattern)) for old, f in entries]
    counts = {}
    for _, k in base:
        counts[k] = counts.get(k, 0) + 1
    used, mapping = {}, {}
    for old, k in base:
        if counts[k] > 1:
            n = used.get(k, 0)
            used[k] = n + 1
            k = k + "abcdefghijklmnopqrstuvwxyz"[n] if n < 26 else "%s%d" % (k, n)
        mapping[old] = k
    return mapping


def rewrite_bib(text, mapping):
    def repl(m):
        return m.group(1) + mapping.get(m.group(3), m.group(3)) + m.group(4)
    return _ENTRY.sub(repl, text)


def rewrite_tex(text, mapping):
    """Replace keys inside every \\cite-like command. Returns (new_text, number_of_replacements)."""
    count = 0

    def repl(m):
        nonlocal count
        keys = []
        for k in m.group(2).split(","):
            stripped = k.strip()
            if stripped in mapping and mapping[stripped] != stripped:
                count += 1
                k = k.replace(stripped, mapping[stripped])
            keys.append(k)
        return m.group(1) + ",".join(keys) + m.group(3)
    return _CITE.sub(repl, text), count
