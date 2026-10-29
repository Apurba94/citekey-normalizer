"""Command-line interface for citekey-normalizer."""
import argparse
import csv
import sys

from .core import plan_keys, read_entries, rewrite_bib, rewrite_tex


def main(argv=None):
    ap = argparse.ArgumentParser(prog="citekey-normalizer",
                                 description="Rename BibTeX keys to a consistent scheme and update .tex files.")
    ap.add_argument("bibfile")
    ap.add_argument("texfiles", nargs="*", help=".tex files whose \\cite commands should be updated")
    ap.add_argument("-p", "--pattern", default="{author}{year}{word}",
                    help="key pattern; placeholders {author} {Author} {authors2} {etal} {year} {word} {words3}")
    ap.add_argument("--apply", action="store_true", help="write changes (default is a dry run)")
    ap.add_argument("--map", help="write old,new key mapping CSV here")
    args = ap.parse_args(argv)

    with open(args.bibfile, encoding="utf-8") as fh:
        bib = fh.read()
    mapping = plan_keys(read_entries(bib), args.pattern)
    changed = {o: n for o, n in mapping.items() if o != n}
    for o, n in changed.items():
        print("%s -> %s" % (o, n))
    if args.map:
        with open(args.map, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["old_key", "new_key"])
            w.writerows(mapping.items())
    total = 0
    for path in args.texfiles:
        with open(path, encoding="utf-8") as fh:
            new, n = rewrite_tex(fh.read(), mapping)
        total += n
        if args.apply and n:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new)
    if args.apply:
        with open(args.bibfile, "w", encoding="utf-8") as fh:
            fh.write(rewrite_bib(bib, mapping))
    print("%d key(s) renamed, %d citation(s) updated%s" % (len(changed), total, "" if args.apply else " (dry run)"),
          file=sys.stderr)
    return 0
