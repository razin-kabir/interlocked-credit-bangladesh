# Reproduce every table, figure and the paper PDF.
#
#   make               analysis + paper
#   make analysis      regenerate paper/tables/*.tex and paper/figures/*.pdf
#   make paper         compile paper/main.pdf (needs latexmk + TeX Live)
#   make verify-data   check the input files against data/checksums.sha256
#   make check         pre-publication privacy checks (run before every push)
#
# Data are read from data/ by default; override with MATS_DATA_DIR and
# BD_DISTRICT_SHP (see data/README.md).

PY ?= uv run --frozen python

# Fixed timestamp so regenerated PDFs are byte-stable (clean git diffs).
export SOURCE_DATE_EPOCH ?= 1767225600
export MPLBACKEND = Agg

.PHONY: all analysis notebook determinants map paper verify-data check clean

all: analysis paper

analysis: notebook determinants map

notebook:
	cd analysis && $(PY) -m nbconvert --to notebook --execute mats_analysis.ipynb \
	    --output-dir ../build --ExecutePreprocessor.timeout=1200

determinants:
	cd analysis && $(PY) credit_determinants.py

map:
	cd analysis && $(PY) credit_map.py

# Recent LaTeX releases (longtable v4.24) raise a recoverable "Infinite glue
# shrinkage found in box being split" error whenever a longtable crosses a page
# (Appendix A). The PDF is correct, but pdflatex exits non-zero, so build with
# -f and then fail on any OTHER error in the log.
paper:
	cd paper && latexmk -pdf -f -interaction=nonstopmode main.tex >/dev/null 2>&1 || true
	@cd paper && test -f main.pdf || { echo "paper/main.pdf was not produced; see paper/main.log"; exit 1; }
	@cd paper && if grep '^!' main.log | grep -v 'Infinite glue shrinkage found in box being split' | grep -q .; then \
	    grep -n -A3 '^!' main.log; echo "LaTeX errors above; see paper/main.log"; exit 1; fi
	@cd paper && if grep -q 'There were undefined' main.log; then \
	    echo "Undefined references/citations; see paper/main.log"; exit 1; fi
	@echo "Built paper/main.pdf"

verify-data:
	$(PY) scripts/verify_data.py

check:
	python3 scripts/check_repo.py

clean:
	rm -rf build
	cd paper && latexmk -c
