# citekey-normalizer

**Give every reference a predictable citation key (`smith2020deep`) and update all
`\cite` commands in your LaTeX sources automatically.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Merged bibliographies end up with keys like `Smith:2020:abc`, `x1`, `10.1038/...` and
`smith_deep_2020` side by side. Inconsistent keys are hard to remember while writing and cause
accidental duplicates. Renaming them by hand means also editing every `\cite`, `\citep` and
`\textcite` in the manuscript, which is exactly the kind of work to automate.

## Features

- Pattern-based keys: `{author}`, `{Author}`, `{authors2}`, `{etal}`, `{year}`, `{word}`, `{words3}`
- Strips LaTeX accents, keeps surname particles (`van der Waals` -> `vanderwaals`), skips title stopwords
- Collisions get `a`, `b`, `c` suffixes
- Updates natbib/biblatex cite commands, including optional arguments and multi-key cites
- Dry run by default; `--apply` writes; `--map` saves an old,new CSV for co-authors

## Usage

```bash
pip install .
citekey-normalizer refs.bib main.tex chapters/*.tex             # preview
citekey-normalizer refs.bib main.tex --apply --map keymap.csv    # rewrite
citekey-normalizer refs.bib -p "{etal}{year}"                    # SmithEtAl2020
```

```python
from citekey_normalizer import read_entries, plan_keys, rewrite_tex
mapping = plan_keys(read_entries(open("refs.bib").read()))
new_tex, n = rewrite_tex(open("main.tex").read(), mapping)
```

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
