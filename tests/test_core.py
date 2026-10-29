import os
import tempfile
import unittest

from citekey_normalizer.cli import main
from citekey_normalizer.core import make_key, plan_keys, read_entries, rewrite_bib, rewrite_tex

BIB = """@article{Smith:2020:abc,
  author = {Smith, John and Doe, Jane and Roe, R.},
  title = {The {Deep} Learning of Proteins},
  year = {2020}
}
@article{x1,
  author = "John Smith",
  title = "Deep thoughts",
  year = 2020
}
@book{vdw,
  author = {Johannes van der Waals},
  title = {On the Continuity},
  year = {1873}
}
"""


class KeyTests(unittest.TestCase):
    def test_default_pattern_skips_stopwords(self):
        self.assertEqual(make_key({"author": "Smith, John", "year": "2020", "title": "The Deep Model"}), "smith2020deep")

    def test_other_placeholders(self):
        f = {"author": "Smith, J. and Doe, J. and Roe, R.", "year": "2021", "title": "A Big New Idea"}
        self.assertEqual(make_key(f, "{etal}{year}"), "SmithEtAl2021")
        self.assertEqual(make_key(f, "{authors2}_{words3}"), "SmithDoe_BigNewIdea")

    def test_accents_particles_and_missing_data(self):
        self.assertEqual(make_key({"author": "M\\\"uller, K.", "year": "", "title": ""}), "mullernd")
        self.assertEqual(make_key({"author": "Johannes van der Waals", "year": "1873", "title": "x"}),
                         "vanderwaals1873x")

    def test_disambiguation_suffixes(self):
        mapping = plan_keys(read_entries(BIB))
        self.assertEqual(mapping["Smith:2020:abc"], "smith2020deepa")
        self.assertEqual(mapping["x1"], "smith2020deepb")
        self.assertEqual(mapping["vdw"], "vanderwaals1873continuity")


class RewriteTests(unittest.TestCase):
    def test_rewrite_bib(self):
        new = rewrite_bib(BIB, {"x1": "smith2020b"})
        self.assertIn("@article{smith2020b,", new)
        self.assertNotIn("{x1,", new)

    def test_rewrite_tex_variants(self):
        tex = r"See \cite{x1}, \citep[p.~3]{a, x1} and \textcite*{vdw}; not \ref{x1}."
        new, n = rewrite_tex(tex, {"x1": "k1", "vdw": "k2", "a": "a"})
        self.assertEqual(n, 3)
        self.assertIn(r"\cite{k1}", new)
        self.assertIn(r"\citep[p.~3]{a, k1}", new)
        self.assertIn(r"\textcite*{k2}", new)
        self.assertIn(r"\ref{x1}", new)

    def test_cli_dry_run_and_apply(self):
        with tempfile.TemporaryDirectory() as d:
            bib, tex = os.path.join(d, "r.bib"), os.path.join(d, "m.tex")
            with open(bib, "w", encoding="utf-8") as fh:
                fh.write(BIB)
            with open(tex, "w", encoding="utf-8") as fh:
                fh.write(r"\cite{x1}")
            main([bib, tex])
            with open(tex, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), r"\cite{x1}")
            main([bib, tex, "--apply", "--map", os.path.join(d, "map.csv")])
            with open(tex, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), r"\cite{smith2020deepb}")
            self.assertTrue(os.path.exists(os.path.join(d, "map.csv")))


if __name__ == "__main__":
    unittest.main()
