# Analysis of Air Pollution Patterns and Hotspots Across India Using Apache Spark

An end-to-end Big Data Analytics mini-project processing **46.9 million historical air-quality observations** from the **XKDR Forum India Air Quality Database** using **Apache Spark (PySpark)**, featuring distributed data cleaning, multi-criteria hotspot ranking, exploratory analytics, time-series forecasting, and an interactive Streamlit dashboard.

---

## Key Highlights

- **Massive Real-World Scale:** Ingests and processes **46,937,170 hourly records** covering the entire calendar year 2024 across **558 CAAQMN monitoring stations** in 28 States and Union Territories.
- **Robust Big Data Pipeline:** Built with **PySpark 3.5.3**, applying schema enforcement, physical bounds validation, and Hive-partitioned Parquet storage (`obs_month=1..12`) with **100.00% physical validity retention**.
- **Multi-Criteria Hotspot Index (MCHI):** Combines chronic exposure, NAAQS 24-hr exceedance frequency, 95th percentile acute severity, and observation density across 518 operational stations.
- **Short-Term PM2.5 Forecasting:** Evaluates chronological holdout models on Delhi NCR (8,760 hours), proving 1-hour ahead regularized Ridge Regression achieves an $R^2$ of **0.985** ($\text{MAE} = 9.17\,\mu\text{g/m}^3$).
- **Interactive Multi-Page Dashboard:** Production-ready **Streamlit** dashboard featuring 8 analytical tabs with geospatial maps, diurnal curves, correlation heatmaps, and downloadable CSV summaries.
- **Executable Notebook Suite:** 5 fully executed Jupyter notebooks (`01` through `05`) with persisted visual and tabular outputs.
- **Comprehensive Project Deliverables:** Complete 22-section project report (`report/project_report.md`) and 12-slide presentation outline (`report/presentation_outline.md`).

---

## Project Folder Structure

```
bda-air-pollution/
├── data/
│   ├── raw/year=2024/month=01..12/data.parquet   # 46.9M raw observations (84.3 MB)
│   ├── sample/sample_jan2024.parquet             # Local validation sample
│   ├── processed/clean_measurements_2024.parquet # 12 Hive-partitioned clean tables
│   └── metadata/                                 # stations.parquet (558), parameters.parquet (15)
├── hadoop/bin/                                   # winutils.exe & hadoop.dll for Windows Spark
├── notebooks/
│   ├── 01_dataset_exploration.ipynb              # Schema discovery & spatial metadata
│   ├── 02_data_cleaning_and_quality.ipynb        # Physical bounds & missing data audit
│   ├── 03_pyspark_big_data_processing.ipynb      # Distributed Spark transformations & Hive write
│   ├── 04_pollution_trends_and_hotspots.ipynb    # Diurnal, seasonal & MCHI hotspot rankings
│   └── 05_advanced_analytics_and_forecasting.ipynb# Correlation matrix & Delhi PM2.5 models
├── src/
│   ├── __init__.py
│   ├── config.py                                 # Environment, paths, winutils & short path handling
│   ├── api_client.py                             # Secure XKDR API client with backoff retries
│   ├── download_data.py                          # Bulk downloader for monthly Parquet files
│   ├── ingest_data.py                            # Ingestion orchestration and verification
│   ├── clean_data.py                             # PySpark cleaning & physical plausibility logic
│   ├── spark_pipeline.py                         # End-to-end distributed Spark processing
│   ├── hotspot_analysis.py                       # MCHI computation & spatial ranking
│   ├── analytics.py                              # Diurnal profiles & Pearson correlation matrices
│   ├── forecasting.py                            # Time-series ML baseline & evaluation
│   └── export_results.py                         # Outputs manifest & consolidated export
├── dashboard/
│   ├── app.py                                    # Streamlit entry point (8 analytical tabs)
│   └── components.py                             # Visual cards, Plotly charts & styling
├── tests/
│   ├── test_api_client.py                        # API client unit tests
│   ├── test_data_cleaning.py                     # PySpark schema & bounds tests
│   └── test_analytics.py                         # Aggregations, symmetry & MCHI tests
├── outputs/
│   ├── charts/                                   # High-resolution PNGs and interactive HTML maps
│   ├── tables/                                   # Curated analytical summaries (CSV)
│   └── metrics/                                  # Pipeline performance & ML metrics (JSON)
├── report/
│   ├── PCCoE_BDA_Mini_Project_Report.pdf         # 8-page formatted project report (PDF)
│   ├── PCCoE_BDA_Mini_Project_Report.docx        # 8-page formatted project report (Word)
│   ├── project_report.md                         # Full 22-section comprehensive report
│   └── presentation_outline.md                   # 12 structured slides with speaking scripts
├── scripts/
│   ├── run_ingestion.py                          # Ingestion execution script
│   ├── run_pipeline.py                           # Full end-to-end pipeline runner
│   ├── run_all_tests.py                          # Pytest test execution script
│   └── build_and_run_all_notebooks.py            # Automated Jupyter notebook builder & runner
├── .env.example                                  # Template for API credentials
├── .gitignore                                    # Git exclusion rules for large data and secrets
├── requirements.txt                              # Pinned Python package dependencies
└── README.md                                     # Project master documentation
```

---

## System Requirements

- **Operating System:** Windows 10/11 (64-bit)
- **Python:** Python 3.10.x or 3.11.x (tested on 3.10.11)
- **Java:** OpenJDK 11 or 17 (tested on OpenJDK 17.0.12)
- **Hardware:** 8 GB RAM minimum (16 GB recommended), 4+ CPU cores, 5 GB free disk space.

---

## Quick Start & Setup Guide

### 1. Clone & Navigate to Project Directory
```powershell
cd "c:\Users\deore\Desktop\bda project"
```

### 2. Configure Python Virtual Environment
```powershell
# Create virtual environment with Python 3.10
py -3.10 -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Register Jupyter Kernel
```powershell
python -m ipykernel install --user --name bda-air-pollution --display-name "Python 3.10 (bda-air-pollution)"
```

### 4. Configure API Credentials
Create a `.env` file in the project root:
```ini
XKDR_API_KEY=your_xkdr_api_key_here
```
*(The repository includes `.env.example` as a template).*

---

## Running the Pipeline

You can run the entire workflow end-to-end or execute individual stages:

### Option A: Execute Complete End-to-End Pipeline
Executes bulk ingestion, distributed PySpark cleaning, aggregation tables, hotspot ranking, exploratory analytics, forecasting, and manifest compilation in a single command:
```powershell
python scripts/run_pipeline.py
```

### Option B: Execute Individual Stages
```powershell
# 1. Download raw observations and metadata from XKDR Forum
python scripts/run_ingestion.py

# 2. Run Spark cleaning and generate analytical summaries
python src/spark_pipeline.py

# 3. Compute Multi-Criteria Hotspot Index (MCHI) rankings
python src/hotspot_analysis.py

# 4. Generate diurnal profiles, seasonal shifts, and correlation matrices
python src/analytics.py

# 5. Run Delhi PM2.5 forecasting experiment
python src/forecasting.py

# 6. Generate project outputs manifest
python src/export_results.py
```

---

## Launching the Streamlit Interactive Dashboard

Launch the web dashboard to interactively explore geospatial hotspot maps, diurnal trends, correlations, and ML predictions:
```powershell
streamlit run dashboard/app.py
```
Then navigate to `http://localhost:8501` in your web browser.

### Dashboard Modules
1. **Executive Overview:** High-level KPIs, national distributions, record summaries.
2. **Interactive Hotspot Map:** Mapbox-powered geospatial map of 518 stations colored by MCHI tier.
3. **Temporal Trend Explorer:** Monthly/seasonal trends filterable by city and pollutant.
4. **Diurnal Pattern Explorer:** 24-hour diurnal curves across primary vs secondary pollutants.
5. **Pollutant Correlation Studio:** Pearson correlation heatmap and pairwise scatter views.
6. **Station Deep-Dive:** Micro-level sensor analysis with percentile breakdowns.
7. **PM2.5 Forecasting Laboratory:** Visualizing holdout predictions vs actual observations.
8. **Data Export & Documentation:** In-browser downloads for curated analytical CSV tables.

---

## Executing Jupyter Notebooks

All 5 notebooks are pre-executed with outputs saved on disk. To launch the Jupyter interface:
```powershell
jupyter lab
# or
jupyter notebook
```
Select the **`Python 3.10 (bda-air-pollution)`** kernel.

To re-run all 5 notebooks programmatically and refresh their outputs:
```powershell
python scripts/build_and_run_all_notebooks.py
```

---

## Running Automated Tests

Run the full pytest suite (10 unit and integration tests):
```powershell
python scripts/run_all_tests.py
# or directly via pytest:
pytest -v
```

### Test Coverage Summary
- `tests/test_api_client.py`: 4 tests (authentication, headers, query params, retry handling)
- `tests/test_data_cleaning.py`: 3 tests (PySpark session, schema validation, bounds filtering)
- `tests/test_analytics.py`: 3 tests (diurnal hourly shapes, correlation bounds, MCHI normalization)

---

## Key Analytical Findings

1. **Severe Regional Disparities:** The Indo-Gangetic Plain accounts for over **85%** of stations in the Severe Hotspot category ($\text{MCHI} \ge 0.70$). Stations such as *Sanjay Palace (Agra)*, *Anand Vihar (Delhi)*, *Sector 62 (Noida)*, and *Loni (Ghaziabad)* exceeded the 24-hour NAAQS safety limit ($60\,\mu\text{g/m}^3$) for over **75%** of all monitored hours in 2024.
2. **Diurnal Bimodal Dynamics:** Combustion pollutants ($\text{PM}_{2.5}, \text{PM}_{10}, \text{NO}_2$) display prominent peaks at 08:00–10:00 IST (morning rush) and 20:00–23:00 IST (heavy commercial transit + nocturnal temperature inversion). In contrast, photochemical Ozone ($\text{O}_3$) peaks between 12:00 and 15:00 IST.
3. **Monsoon Wet Scavenging:** Nationwide $\text{PM}_{2.5}$ drops by **65% to 75%** between July and September due to precipitation washout, dropping to safe baseline levels ($20\text{--}35\,\mu\text{g/m}^3$) before winter stagnation resumes.
4. **Predictive Horizon Limits:** Autoregressive Ridge Regression achieves $R^2 = 0.985$ for 1-hour ahead forecasting. However, predicting beyond 24 hours without Numerical Weather Prediction (NWP) inputs causes accuracy to deteriorate significantly ($R^2 < 0.35$).

---

## Project & Presentation Deliverables

- **Official PDF Project Report:** [`report/PCCoE_BDA_Mini_Project_Report.pdf`](file:///report/PCCoE_BDA_Mini_Project_Report.pdf) (8-page formatted report matching the PCCoE submission layout).
- **Official Word (.docx) Project Report:** [`report/PCCoE_BDA_Mini_Project_Report.docx`](file:///report/PCCoE_BDA_Mini_Project_Report.docx) (Editable Word document with embedded figures, tables, and typography).
- **Comprehensive Project Report (Markdown):** [`report/project_report.md`](file:///report/project_report.md) (22 detailed technical sections).
- **Presentation Outline:** [`report/presentation_outline.md`](file:///report/presentation_outline.md) (12 structured slides with speaking scripts and diagrams).

---

## Troubleshooting on Windows

1. **Hadoop / winutils.exe Error:** If you encounter `java.io.IOException: HADOOP_HOME and hadoop.home.dir are unset`, ensure `hadoop/bin/winutils.exe` and `hadoop.dll` are present. `src/config.py` automatically configures `HADOOP_HOME` to this directory.
2. **Space in Path (`bda project`):** Spark batch scripts can misinterpret spaces in folder names. `src/config.py` automatically resolves Windows 8.3 short paths (e.g., `BDAPRO~1`) for `PYSPARK_PYTHON` and `PYSPARK_DRIVER_PYTHON`.
3. **Java Version:** Verify that Java 11 or 17 is installed by running `java -version`. Ensure `JAVA_HOME` points to your JDK installation.

---

## Data Attribution & License

- **Data Source:** Historical observations are provided by the [XKDR Forum India Air Quality Database](https://airquality.xkdr.org/), which compiles Continuous Ambient Air Quality Monitoring Network (CAAQMN) data from the Central Pollution Control Board (CPCB), Government of India.
- **Project License:** Open-source for academic research and educational evaluation.
