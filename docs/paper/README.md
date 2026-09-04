# AARFLingo paper

Manuscript: [PAPER.md](PAPER.md) (canonical prose) and [aarflingo.tex](aarflingo.tex) (arXiv source).

Protocol (reviewer can run without the prose): [METHODS.md](METHODS.md), generated [RESULTS.md](RESULTS.md), [DATASHEET.md](DATASHEET.md), [reproduce.md](reproduce.md).

This preprint does **not** claim 95% home-dog accuracy. `python3 scripts/v1_gate.py --require-bar` fails until `data/dog/eval/dog_split.jsonl` exists.

```bash
# regenerate the results table
python3 scripts/v1_gate.py

# PDF (TeX Live: pdflatex + bibtex)
make paper
# or
cd docs/paper && pdflatex aarflingo.tex && bibtex aarflingo && pdflatex aarflingo.tex && pdflatex aarflingo.tex
```

Built file: [aarflingo.pdf](aarflingo.pdf).
