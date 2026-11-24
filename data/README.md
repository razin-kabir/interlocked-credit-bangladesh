# Input data (not included)

Nothing in this folder except this file and `checksums.sha256` is tracked by git.

## 1. MATS 2018 trader survey

The 2018 Bangladesh Millers and Traders Survey (MATS) was conducted by the International Food
Policy Research Institute (IFPRI). The microdata are **not publicly released**.
To request access, contact the corresponding author or IFPRI.

The analysis needs five cleaned trader modules:

| File | Used for | Variables used |
|---|---|---|
| `traders_modD_D9-D10.dta` | credit arrangements | `tempid`, `season`, `a04` (district code), `a05` (upazila code), `b09`, `b10`, `b11`, `d35`–`d47` |
| `traders_modD_D5.dta` | monthly paddy procurement prices | `tempid`, `season`, `month`, `pprocmprice` |
| `traders_modD_D3.dta` | dominant paddy variety | `tempid`, `season`, `pproctype`, `pprocqty` |
| `traders_modAB.dta` | Table 6 only | `tempid`, `b01` (age), `b03` (schooling), `b04` (subsidiary), `b05` (ownership); **no other columns are read** |
| `traders_modC_C1.dta` | Table 6 only | `tempid`, `c01` (year business established) |

Place them like this, or set `MATS_DATA_DIR` to the folder that contains `trader_data/`:

```
data/mats_2018/trader_data/clean/traders_modD_D9-D10.dta
data/mats_2018/trader_data/clean/traders_modD_D5.dta
data/mats_2018/trader_data/clean/traders_modD_D3.dta
data/mats_2018/trader_data/clean/traders_modAB.dta
data/mats_2018/trader_data/clean/traders_modC_C1.dta
```

## 2. District boundaries (Figure 2 only)

The map uses the 2022 district boundaries published by the Bangladesh Bureau of Statistics
(BBS): `district2022.shp` with its `.shx`, `.dbf`, `.prj` and `.cpg` files. Its `DISTRICT_C`
field holds the 2-digit BBS district code, which matches survey variable `a04`. Any district polygon file
carrying that code works if the field is named `DISTRICT_C`.

Place it at `data/shapefiles/district2022.shp`, or set `BD_DISTRICT_SHP` to its path.

## 3. Verifying your copy

`checksums.sha256` holds the SHA-256 hashes of the exact files used for the published
results. Run:

```bash
make verify-data
```
