"""Who uses supplier credit? Trader characteristics and credit uptake.

Generates:
  paper/figures/fig5_credit_dist.pdf    -- Figure 3: upazila-season credit share distribution
  paper/tables/tab6_determinants.tex    -- Table 6: correlates of credit use (logit AME + LPM)

Trader characteristics (variable labels from the MATS 2018 codebook):
  b01  age (years)
  b03  highest schooling completed (ordinal category; converted to approx. years below)
  b04  "Is this business a subsidiary of some other business?" (1 = yes, 2 = no)
  b05  ownership type (1 = sole ownership, 2 = partnership)
  c01  year the trading business was established (module C1) -> years in business
"""
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from common import FIGURES, SURVEY_YEAR, TABLES, fmt_c, fmt_se, trader_file, write_tex

warnings.filterwarnings("ignore")
FIGURES.mkdir(parents=True, exist_ok=True)

# b03 schooling category -> approximate completed years of schooling.
# Bangladesh: SSC after class 10, HSC after class 12, bachelor's ~14, master's ~16.
# Vocational/technical (11) and Other (12) are not ordered and are set to missing.
SCHOOLING_YEARS = {0: 0, 1: 2.5, 2: 5, 3: 6, 4: 7, 5: 8, 6: 9, 7: 10, 8: 12, 9: 14, 10: 16}

# ── Load data ─────────────────────────────────────────────────────────────────
d9 = pd.read_stata(trader_file("traders_modD_D9-D10.dta"), convert_categoricals=False)
# Only the non-identifying characteristics are read from module AB / C1.
ab = pd.read_stata(trader_file("traders_modAB.dta"), convert_categoricals=False,
                   columns=["tempid", "b01", "b03", "b04", "b05"])
c1 = pd.read_stata(trader_file("traders_modC_C1.dta"), convert_categoricals=False,
                   columns=["tempid", "c01"])

d9["any_credit"] = d9["d35"].map({1: 0, 2: 1, 3: 1})

# Paddy trader-seasons (unique per trader per season)
ts = d9.loc[d9["b09"].isin([1, 3]), ["tempid", "season", "a04", "a05", "b10", "any_credit"]].copy()
ts["upazila_str"] = ts["a05"].astype(str)
ts["season_str"] = ts["season"].astype(str)
print(f"Paddy trader-seasons: {len(ts):,}")

chars = ab.merge(c1, on="tempid", how="left")
chars["age"] = chars["b01"]
chars["educ_yrs"] = chars["b03"].map(SCHOOLING_YEARS)
chars["subsidiary"] = chars["b04"].map({1: 1.0, 2: 0.0})
chars["sole_owner"] = chars["b05"].map({1: 1.0, 2: 0.0})
chars["yrs_biz"] = SURVEY_YEAR - chars["c01"]
chars = chars[["tempid", "age", "educ_yrs", "subsidiary", "sole_owner", "yrs_biz"]]

ts2 = ts.merge(chars, on="tempid", how="left")
ts2["is_aratdar"] = (ts2["b10"] == 2).astype(float)
ts2["is_broker"] = (ts2["b10"] == 3).astype(float)

# ── Figure 5: Upazila-season credit share distribution ───────────────────────
upz_share = (ts2.groupby(["upazila_str", "season_str"])["any_credit"]
             .mean().reset_index().rename(columns={"any_credit": "share"}))
pct_100 = (upz_share["share"] == 1.0).mean() * 100

fig, ax = plt.subplots(figsize=(6, 4))
bins = np.arange(0, 1.05, 0.1)
ax.hist(upz_share["share"], bins=bins, color="#2c7bb6", edgecolor="white",
        linewidth=0.6, alpha=0.85)
ax.axvline(upz_share["share"].mean(), color="#d7191c", lw=1.5,
           linestyle="--", label=f"Mean = {upz_share['share'].mean():.2f}")
ax.axvline(upz_share["share"].median(), color="#1a9641", lw=1.5,
           linestyle=":", label=f"Median = {upz_share['share'].median():.2f}")
ax.set_xlabel("Fraction of traders with supplier credit", fontsize=11)
ax.set_ylabel("Number of upazila-seasons", fontsize=11)
ax.set_title("Distribution of Local Credit Market Intensity", fontsize=12)
ax.legend(fontsize=9)
ax.annotate(f"{pct_100:.0f}% of\nupazila-seasons\nhave share = 1.0",
            xy=(1.0, upz_share["share"].eq(1.0).sum()),
            xytext=(0.72, upz_share["share"].eq(1.0).sum() * 0.75),
            arrowprops=dict(arrowstyle="->", color="black", lw=1),
            fontsize=8.5, ha="center")
plt.tight_layout()
plt.savefig(FIGURES / "fig5_credit_dist.pdf", bbox_inches="tight")
plt.close()
print(f"Saved fig5_credit_dist.pdf  (pct_100={pct_100:.1f}%)")

# ── Table 6: Credit determinants ─────────────────────────────────────────────
key_vars = ["age_c", "educ_c", "yrs_c", "subsidiary", "sole_owner", "is_aratdar", "is_broker"]
labels = {
    "age_c":      "Age (years, mean-centred)",
    "educ_c":     "Schooling (approx.\\ years, mean-centred)",
    "yrs_c":      "Years in business (mean-centred)",
    "subsidiary": "Subsidiary of another business",
    "sole_owner": "Sole proprietorship",
    "is_aratdar": "Trader type: Aratdar",
    "is_broker":  "Trader type: Broker/intermediary",
}

det = ts2.dropna(subset=["any_credit", "age", "educ_yrs", "yrs_biz",
                         "subsidiary", "sole_owner", "is_aratdar", "is_broker"]).copy()
det["age_c"] = det["age"] - det["age"].mean()
det["educ_c"] = det["educ_yrs"] - det["educ_yrs"].mean()
det["yrs_c"] = det["yrs_biz"] - det["yrs_biz"].mean()

# Every broker trader-season reports credit, so the broker dummy perfectly
# predicts the outcome and its logit coefficient is not identified.
broker_separated = det.loc[det["is_broker"] == 1, "any_credit"].nunique() == 1
logit_vars = [v for v in key_vars if not (v == "is_broker" and broker_separated)]
lpm_vars = key_vars

m_lo = smf.logit("any_credit ~ " + " + ".join(logit_vars) + " + C(season_str)",
                 data=det if not broker_separated else det[det["is_broker"] == 0]).fit(disp=0)
m_lp = smf.ols("any_credit ~ " + " + ".join(lpm_vars) + " + C(season_str)",
               data=det).fit(cov_type="cluster", cov_kwds={"groups": det["upazila_str"]})

me = m_lo.get_margeff(at="overall")  # average marginal effects
me_tab = pd.DataFrame({"me": me.margeff, "se": me.margeff_se, "p": me.pvalues},
                      index=m_lo.params.index[1:])

print(f"\nDeterminants sample N={len(det):,}  (logit N={int(m_lo.nobs):,})")
for v in key_vars:
    c, se, p = m_lp.params[v], m_lp.bse[v], m_lp.pvalues[v]
    print(f"  {v:12s}  LPM {c:+.3f} ({se:.3f}) p={p:.3f}", end="")
    if v in me_tab.index:
        print(f"   Logit AME {me_tab.loc[v, 'me']:+.3f} ({me_tab.loc[v, 'se']:.3f})")
    else:
        print("   Logit AME n/a (perfect prediction)")

rows = [
    r"\begin{tabular}{lcc}",
    r"\toprule",
    r"& Logit (AME) & LPM \\",
    r"& (1) & (2) \\",
    r"\midrule",
    r"\multicolumn{3}{l}{\textit{Trader characteristics}} \\",
    r"\addlinespace[2pt]",
]
for v in key_vars:
    if v in me_tab.index:
        col1 = fmt_c(me_tab.loc[v, "me"], me_tab.loc[v, "p"], 3)
        col1s = fmt_se(me_tab.loc[v, "se"], 3)
    else:
        col1, col1s = "{---}", ""
    col2 = fmt_c(m_lp.params[v], m_lp.pvalues[v], 3)
    col2s = fmt_se(m_lp.bse[v], 3)
    rows += [f"{labels[v]} & {col1} & {col2} \\\\", f"& {col1s} & {col2s} \\\\", r"\addlinespace[2pt]"]

broker_note = (r" All broker/intermediary trader-seasons report credit, so the broker"
               r" dummy perfectly predicts the outcome; these observations are dropped"
               r" from the logit." if broker_separated else "")
rows += [
    r"\midrule",
    r"Season FEs & Yes & Yes \\",
    f"Observations & {int(m_lo.nobs):,} & {int(m_lp.nobs):,} \\\\",
    r"\addlinespace[2pt]",
    r"\multicolumn{3}{p{0.72\textwidth}}{\footnotesize \textit{Notes:}"
    r" Dependent variable: binary indicator for any supplier credit (trader-season)."
    r" Column (1): logit average marginal effects."
    r" Column (2): linear probability model, SE clustered at upazila level."
    r" Schooling converts the highest level completed to approximate years."
    r" Years in business $= 2018 -$ year the business was established."
    r" Reference categories: partnership (ownership), Faria/bepari (trader type)."
    + broker_note +
    r" $^{*}p<0.10$, $^{**}p<0.05$, $^{***}p<0.01$.} \\",
    r"\bottomrule",
    r"\end{tabular}",
]
write_tex(TABLES / "tab6_determinants.tex", rows)
