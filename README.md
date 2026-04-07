# EBITDA Leak Analysis — HoReCa Data Pipeline

End-to-end data cleaning and business intelligence pipeline for the restaurant industry.  
The project identifies EBITDA leak sources by comparing real vs theoretical ingredient consumption, calculates Food Cost % per dish, and flags pricing anomalies against market benchmarks.

---

## Business Problem

Restaurants typically lose 2–5% EBITDA annually due to:
- Food waste and spoilage
- Recipe deviation (over/under-portioning)
- Inventory counting inaccuracies
- Purchase price variance vs market benchmark

This pipeline quantifies each leak source in euros, giving management actionable priorities.

---

## Dataset

Four synthetic dirty datasets simulating a real Italian restaurant (2023–2024):

| File | Description | Rows |
|---|---|---|
| `raw_sales_pos.csv` | POS transactions | 64,654 |
| `supplier_invoices.csv` | Supplier invoices | 1,610 |
| `recipe_book_unstandardized.csv` | Recipe book | 64 |
| `inventory_stock.csv` | Monthly stock counts | 576 |
| `benchmark_ingredienti_horeca.csv` | Market reference prices (CAR Roma, ISMEA, CLAL) | 115 |

Datasets contain intentional data quality issues: mixed units of measure, inconsistent ingredient names, price typos, missing values — designed to simulate real-world HoReCa data extraction.

---

## Pipeline Architecture

```
raw_sales_pos.csv       ──┐
supplier_invoices.csv   ──┤──► Data Cleaning & Standardization ──► EBITDA Leak (€)
recipe_book.csv         ──┤──► Fuzzy Matching & Name Unification ──► Food Cost % per dish
inventory_stock.csv     ──┘
benchmark.csv           ──────► Price Validation & WAP Fallback
```

### Steps

1. **Basic cleaning** — lowercase, strip whitespace, MAPPING_DICT substitution
2. **Unit error detection** — business rule: price >€10 with unit `g` → convert to `kg`
3. **Unit standardization** — map all quantities to `kg` / `lt`
4. **Quantity exception management** — CONVERSION_MAP for `pz` → `kg` (burrata 125g/pz, uova 60g/pz)
5. **Outlier detection** — IQR-based, excludes premium categories (zafferano, tartufo)
6. **Price substitution** — outlier prices replaced with benchmark market prices
7. **Fuzzy matching** — `thefuzz` library unifies 150+ ingredient name variations against benchmark
8. **WAP calculation** — Weighted Average Price per ingredient per month
9. **EBITDA leak** — Real consumption (opening stock + purchases − closing stock) vs Theoretical consumption (recipe × orders sold) × WAP
10. **Food Cost %** — aggregated per transaction and dish, using benchmark prices

---

## Tech Stack

- **Python** — pandas, numpy, matplotlib, seaborn
- **thefuzz** — fuzzy string matching
- **Jupyter Notebook** — interactive pipeline with markdown documentation
- **Benchmark data** — CAR Roma (ortofruit/fish), ISMEA (meat), CLAL (dairy)

---

## Key Results — February 2023 Sample

> Single-month analysis. Pipeline designed for full monthly loop across 2023–2024.

### EBITDA Leak

| Ingredient | Leak (€) | Qty | WAP |
|---|---|---|---|
| Burrata | €791 | 33.49 kg | €23.62/kg |
| Salmone fresco filetti | €559 | 33.98 kg | €16.45/kg |
| Filetto di manzo | €532 | 14.68 kg | €36.23/kg |
| Vongole veraci fresche | €517 | 53.51 kg | €9.67/kg |
| Vino rosso da cucina | €270 | 42.00 kg | €6.43/kg |

**Total net EBITDA leak: −€71.73** (positive leaks partially offset by under-portioning)  
**Missing WAP: 0** (full coverage via invoice data + benchmark fallback)

### Food Cost % — Full Dataset 2023–2024

**Overall FC%: 19.9%** — below industry benchmark of 25–30%, driven by high-margin pasta and antipasti.

| Dish | FC% | Strategic Signal |
|---|---|---|
| Bistecca alla fiorentina | 41% | Premium — protect margin via pricing |
| Branzino al forno | 28% | Balanced |
| Tiramisu | 26% | Balanced |
| Spaghetti alle vongole | 9% | High-margin — prioritize upsell |
| Bruschette / Tagliere | 4–5% | High-margin — prioritize upsell |

### Data Quality Issues Resolved

1. Unit inconsistencies (`bt`, `pz`, `cassa`) across all 4 sources
2. 150+ ingredient name variations unified via fuzzy matching
3. Price typos corrected (e.g. €950/unit → €9.50)
4. Unrealistic synthetic prices replaced with real market benchmarks
5. Missing WAP covered via benchmark fallback

---

## Business Recommendations

**Immediate actions (waste):**
- **Burrata** → reduce order frequency, improve FIFO rotation
- **Salmone / Filetto** → stricter portioning control, mise en place procedures

**Menu strategy:**
- Upsell pasta and antipasti (FC% 4–11%) — highest margin contribution
- Protect premium protein pricing (bistecca, tagliata) — high FC% is structurally justified

**Next steps for production:**
- [ ] Monthly loop — extend leak analysis to full 2023–2024 dataset
- [ ] Price anomaly flag — WARNING/CRITICAL at ±25% vs benchmark
- [ ] Automated alerts — trigger when single-ingredient leak > €500/month
- [ ] Dashboard — Tableau/PowerBI for real-time monitoring
- [ ] Forecasting — Prophet/ARIMA for predictive ordering

---

## Project Structure

```
├── Data/
|   ├── raw_sales_pos.csv
│   ├── supplier_invoices.csv
│   ├── recipe_book_unstandardized.csv
│   ├── inventory_stock.csv
│   └── benchmark_ingredienti_horeca.csv
├── Notebook/
│   └── ebitda_pipeline.ipynb
├── Src/
│   └── utils.py
├── Requirements/
└── README.md
```

---

## Author

**Giovanni Lo Presti** — Ex-chef turned Data Analyst.  
Combining 15+ years of restaurant operations experience with Python, SQL, and BI tools  
to build analytics solutions for the HoReCa sector.

[GitHub](https://github.com/GiaLop) · [LinkedIn](https://www.linkedin.com/in/giovanni-lo-presti-b15b7761/)
