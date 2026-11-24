# Interlocked Credit in Bangladesh's Rice Trading Sector

Replication package for

> Kabir, R. (2026). *Interlocked Credit in Agricultural Commodity Markets: Prevalence,
> Structure, and Market Implications in Bangladesh's Rice Trading Sector.* Working paper.

The paper uses the 2018 Bangladesh Millers and Traders Survey (MATS) to document how common
supplier credit is among paddy traders and whether it depresses procurement prices.
Main findings:

- 82% of paddy trader-seasons involve supplier credit.
- There is no significant within-market price discount (OLS and IV).
- The minority who pay an explicit credit premium face a median implied annual rate of 51%.

The compiled paper is [`paper/main.pdf`](paper/main.pdf).

## Repository layout

```
analysis/
  mats_analysis.ipynb      main analysis: descriptives, OLS, IV, heterogeneity; writes most tables/figures
  credit_determinants.py   Table 6 (correlates of credit use) and Figure 3
  credit_map.py            Figure 2 (district map)
  common.py                paths, sample restrictions, LaTeX helpers
paper/
  main.tex, references.bib
  tables/  figures/        generated outputs, \input{} by main.tex
  main.pdf                 compiled paper
data/
  README.md                how to obtain the input data (not included)
  checksums.sha256         SHA-256 of the exact input files used
scripts/
  check_repo.py            pre-publication privacy check
  verify_data.py           checks your input files against data/checksums.sha256
```

## Data

The MATS 2018 microdata are **not included**: they are not publicly released, and they contain
respondents' names, locations and GPS coordinates. [`data/README.md`](data/README.md) lists the
files you need, the variables used from each, and how to request access.

## Reproducing the results

**Requirements:** [uv](https://docs.astral.sh/uv/) (it installs Python ≥ 3.11 and the exact
package versions in `uv.lock`), a LaTeX distribution with `latexmk` and the `elsarticle`
class (TeX Live or MiKTeX), and `make`.

```bash
git clone https://github.com/razin-kabir/interlocked-credit-bangladesh.git
cd interlocked-credit-bangladesh
uv sync --frozen                      # create .venv with pinned dependencies

# point to the data (or place it under data/ as described in data/README.md)
export MATS_DATA_DIR=/path/to/mats_2018
export BD_DISTRICT_SHP=/path/to/district2022.shp

make verify-data                      # optional: confirm you have the same input files
make                                  # all tables + figures, then paper/main.pdf
```

The whole pipeline takes under a minute on a laptop. Outputs are deterministic: re-running
produces byte-identical tables and figures.

<details>
<summary>Without <code>make</code> (e.g. Windows PowerShell)</summary>

```powershell
uv sync --frozen
$env:MATS_DATA_DIR = "C:\path\to\mats_2018"
$env:BD_DISTRICT_SHP = "C:\path\to\district2022.shp"
cd analysis
uv run python -m nbconvert --to notebook --execute mats_analysis.ipynb --output-dir ../build
uv run python credit_determinants.py
uv run python credit_map.py
cd ../paper
latexmk -pdf -f main.tex
```
</details>

### Where each result comes from

| Paper | File in `paper/` | Produced by |
|---|---|---|
| Table 1 (comparison with literature) | `tables/tab1_comparison.tex` | hand-written |
| Tables 2–5 (summary statistics; credit by type, season, district) | `tables/tab2_*.tex` … `tab5_*.tex` | `mats_analysis.ipynb` |
| Table 6 (correlates of credit use) | `tables/tab6_determinants.tex` | `credit_determinants.py` |
| Tables 7–10 (OLS, IV, heterogeneity, price variance) | `tables/tab7_*.tex` … `tab10_*.tex` | `mats_analysis.ipynb` |
| Appendix tables (upazila detail, IV first stage) | `tables/tab_app_*.tex` | `mats_analysis.ipynb` |
| Figure 1 (credit prevalence and payment mix) | `figures/fig1_credit_prevalence.pdf` | `mats_analysis.ipynb` |
| Figure 2 (district map) | `figures/fig4_credit_map.pdf` | `credit_map.py` |
| Figure 3 (local credit market intensity) | `figures/fig5_credit_dist.pdf` | `credit_determinants.py` |

`fig2_payment_mix.pdf` and `fig3_implicit_rate.pdf` are supplementary figures that the
notebook also produces; they are not in the paper.

**Known LaTeX issue.** Recent LaTeX releases (longtable v4.24) report a recoverable
"Infinite glue shrinkage found in box being split" error whenever a longtable crosses a page
(Appendix A). The PDF is correct. `make paper` tolerates that one error and fails on any other.

## Privacy

This repository is checked to contain no personally identifying information.

- No microdata, shapefiles or derived row-level files are committed (`.gitignore` blocks them).
- The notebook is committed **without outputs**.
- The code never reads names, addresses, GPS, interviewer or gender fields.
  From the module that contains them, it reads only age, schooling, ownership type and the
  subsidiary flag.
- Every published district or upazila statistic pools at least three distinct traders.
  Smaller units are dropped from tables and hatched on the map (`MIN_TRADERS` in
  `analysis/common.py`).

Run `make check` before every commit. It scans everything git would publish for data files,
notebook outputs, local paths, e-mail addresses, phone numbers, GPS coordinates and references
to identifying survey variables. The same check runs on GitHub for every push.

## Citation

See [`CITATION.cff`](CITATION.cff). The survey itself is described in Dorosh, Minot, Kabir and
Hossain (2021), *Private sector rice stocks in Bangladesh: Estimates from the Bangladesh
Millers' and Traders' Survey (MATS) 2018*, IFPRI, <https://hdl.handle.net/10568/143610>.

## License

Code is released under the [MIT License](LICENSE). The paper (`paper/main.tex`,
`paper/main.pdf`) is © the author, all rights reserved, and is shared as a working paper.
