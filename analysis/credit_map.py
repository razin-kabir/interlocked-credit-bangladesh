"""Figure 2 of the paper: district map of supplier-credit prevalence among paddy traders.

Generates paper/figures/fig4_credit_map.pdf. Districts with fewer than MIN_TRADERS
sampled traders are hatched instead of coloured. Needs the 2022 district boundary
shapefile (BD_DISTRICT_SHP; see data/README.md) whose DISTRICT_C field holds the
2-digit BBS district code that matches survey variable a04.
"""
import warnings

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.cm import ScalarMappable
from matplotlib.colors import BoundaryNorm

from common import DISTRICT_SHP, FIGURES, MIN_TRADERS, trader_file

warnings.filterwarnings("ignore")
FIGURES.mkdir(parents=True, exist_ok=True)

if not DISTRICT_SHP.exists():
    raise FileNotFoundError(
        f"{DISTRICT_SHP} not found. See data/README.md and set BD_DISTRICT_SHP."
    )

d9 = pd.read_stata(trader_file("traders_modD_D9-D10.dta"), convert_categoricals=False)
d9["any_credit"] = d9["d35"].map({1: 0, 2: 1, 3: 1})
paddy = d9[d9["b09"].isin([1, 3])].copy()

dist_cr = (paddy.dropna(subset=["any_credit"]).groupby("a04")
           .agg(pct=("any_credit", lambda x: x.mean() * 100),
                n=("any_credit", "count"),
                n_traders=("tempid", "nunique"))
           .reset_index()
           .rename(columns={"a04": "dist_int"}))

# Confidentiality: districts with fewer than MIN_TRADERS traders are not coloured.
dist_cr["suppressed"] = dist_cr["n_traders"] < MIN_TRADERS
dist_cr.loc[dist_cr["suppressed"], "pct"] = float("nan")

shp = gpd.read_file(DISTRICT_SHP)
shp["dist_int"] = pd.to_numeric(shp["DISTRICT_C"], errors="coerce").astype("Int64")
shp_m = shp.merge(dist_cr, on="dist_int", how="left")
shp_m["suppressed"] = shp_m["suppressed"].astype("boolean").fillna(False).astype(bool)
print(f"Sampled {shp_m['n'].notna().sum()}/{len(shp_m)} districts; "
      f"{int(shp_m['suppressed'].sum())} suppressed (< {MIN_TRADERS} traders)")

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(1, 1, figsize=(6.5, 8))

# Districts not in the MATS sample
not_sampled = shp_m["n"].isna()
shp_m[not_sampled].plot(ax=ax, color="#f0f0f0", linewidth=0.4, edgecolor="#888888")
# Sampled, but too few traders to publish
shp_m[shp_m["suppressed"]].plot(ax=ax, color="#d9d9d9", hatch="////",
                                linewidth=0.4, edgecolor="#888888")

bounds = [0, 25, 50, 75, 90, 100]
cmap = matplotlib.colormaps["RdYlGn"].resampled(len(bounds) - 1)
norm = BoundaryNorm(bounds, cmap.N)

has_data = shp_m[shp_m["pct"].notna()]
has_data.plot(ax=ax, color=[cmap(norm(v)) for v in has_data["pct"]],
              linewidth=0.4, edgecolor="#666666")

sm = ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, orientation="vertical", fraction=0.03, pad=0.02, shrink=0.55)
cbar.set_label("Any-credit prevalence (%)", fontsize=9)
cbar.set_ticks(bounds)

no_data_patch = mpatches.Patch(facecolor="#f0f0f0", edgecolor="#888888", label="Not sampled")
suppressed_patch = mpatches.Patch(facecolor="#d9d9d9", edgecolor="#888888", hatch="////",
                                  label=f"Fewer than {MIN_TRADERS} traders (suppressed)")
ax.legend(handles=[no_data_patch, suppressed_patch], loc="lower left", fontsize=8)

ax.set_axis_off()
ax.set_title("Supplier Credit Prevalence by District\n(Paddy Traders, MATS 2018)", fontsize=11, pad=8)

plt.tight_layout()
plt.savefig(FIGURES / "fig4_credit_map.pdf", bbox_inches="tight", dpi=200)
plt.close()
print("Saved paper/figures/fig4_credit_map.pdf")
