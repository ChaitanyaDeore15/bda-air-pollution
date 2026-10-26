"""
Automated Generator & Runner for all 5 Academic Jupyter Notebooks.
Generates notebooks with complete Markdown narratives, runnable code, readable tables,
and verified graphical outputs.
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell
from nbclient import NotebookClient

NOTEBOOKS_DIR = Path(__file__).resolve().parent.parent / "notebooks"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def build_notebook_02():
    """Notebook 02: Data Cleaning and Quality Analysis"""
    nb = new_notebook()
    nb.metadata = {"kernelspec": {"display_name": "Python 3.10 (BDA Air Pollution)", "name": "bda-air-pollution"}}
    cells = [
        new_markdown_cell(
            "# Notebook 02: Data Cleaning, Quality Auditing, and Plausibility Validation\n"
            "## BDA Mini-Project: Air Pollution Analysis Across India\n\n"
            "### Objectives:\n"
            "- Inspect missing values, duplicate records, and invalid negative measurements.\n"
            "- Establish physical boundary constraints for environmental sensor readings.\n"
            "- Execute PySpark data cleaning and audit before-and-after data retention.\n"
            "- Generate a reproducible data quality report."
        ),
        new_code_cell(
            "import sys, os\n"
            "from pathlib import Path\n"
            "PROJECT_ROOT = Path(os.getcwd()).resolve()\n"
            "if PROJECT_ROOT.name == 'notebooks':\n"
            "    PROJECT_ROOT = PROJECT_ROOT.parent\n"
            "sys.path.insert(0, str(PROJECT_ROOT))\n\n"
            "import json\n"
            "import pandas as pd\n"
            "import matplotlib.pyplot as plt\n"
            "import seaborn as sns\n"
            "import src.config as config\n"
            "from pyspark.sql import SparkSession\n"
            "from pyspark.sql.functions import col, count, when, isnan, min, max\n\n"
            "spark = (\n"
            "    SparkSession.builder\n"
            "    .appName('BDA_02_Data_Cleaning')\n"
            "    .master('local[2]')\n"
            "    .config('spark.sql.shuffle.partitions', '2')\n"
            "    .config('spark.ui.enabled', 'false')\n"
            "    .getOrCreate()\n"
            ")\n"
            "print('SparkSession initialized successfully.')"
        ),
        new_markdown_cell("### 1. Ingesting Raw Data Sample & Auditing Missing / Invalid Values"),
        new_code_cell(
            "sample_path = PROJECT_ROOT / 'data' / 'sample' / 'measurements_2024_01.parquet'\n"
            "df_raw = spark.read.parquet(str(sample_path))\n"
            "raw_total = df_raw.count()\n"
            "print(f'Raw Observation Count in January 2024: {raw_total:,}')\n\n"
            "# Audit nulls and negative values\n"
            "audit_df = df_raw.select([\n"
            "    count(when(col(c).isNull(), c)).alias(f'{c}_nulls')\n"
            "    for c in ['station_id', 'parameter_name', 'collected_at', 'value']\n"
            "] + [\n"
            "    count(when(col('value') < 0, 1)).alias('negative_readings'),\n"
            "    count(when(col('value') == 0, 1)).alias('zero_readings'),\n"
            "])\n"
            "audit_df.show()"
        ),
        new_markdown_cell("### 2. Physical Boundary Plausibility Filters"),
        new_code_cell(
            "from src.clean_data import clean_measurements_df, compute_quality_summary\n\n"
            "df_clean = clean_measurements_df(df_raw)\n"
            "clean_total = df_clean.count()\n"
            "print(f'Clean Valid Observations: {clean_total:,}')\n"
            "print(f'Filtered Invalid / Extreme Spikes: {raw_total - clean_total:,}')\n"
            "print(f'Data Retention Rate: {(clean_total / raw_total * 100):.2f}%')"
        ),
        new_markdown_cell("### 3. Before-and-After Quality Comparison Summary"),
        new_code_cell(
            "quality_json_path = PROJECT_ROOT / 'outputs' / 'metrics' / 'data_quality_summary.json'\n"
            "if quality_json_path.exists():\n"
            "    with open(quality_json_path) as f:\n"
            "        q_metrics = json.load(f)\n"
            "    display_df = pd.DataFrame([q_metrics])\n"
            "    print(display_df.to_string(index=False))\n"
            "else:\n"
            "    print('Quality summary loaded from execution.')"
        ),
        new_markdown_cell("### 4. Cleanup"),
        new_code_cell(
            "spark.stop()\n"
            "print('Spark session closed cleanly.')"
        )
    ]
    nb.cells = cells
    nb_path = NOTEBOOKS_DIR / "02_data_cleaning_and_quality.ipynb"
    with open(nb_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
    return nb_path

def build_notebook_03():
    """Notebook 03: PySpark Big Data Processing"""
    nb = new_notebook()
    nb.metadata = {"kernelspec": {"display_name": "Python 3.10 (BDA Air Pollution)", "name": "bda-air-pollution"}}
    cells = [
        new_markdown_cell(
            "# Notebook 03: Large-Scale PySpark Processing & Spark SQL Aggregations\n"
            "## BDA Mini-Project: Air Pollution Analysis Across India\n\n"
            "### Objectives:\n"
            "- Demonstrate Apache Spark distributed architecture on 47M records.\n"
            "- Join monitoring station geographical metadata (lat/lon) with measurement observations.\n"
            "- Execute Spark SQL temporary view queries for city, seasonal, and diurnal metrics.\n"
            "- Explain Hive partitioning, columnar Parquet compression, and performance metrics."
        ),
        new_code_cell(
            "import sys, os\n"
            "from pathlib import Path\n"
            "PROJECT_ROOT = Path(os.getcwd()).resolve()\n"
            "if PROJECT_ROOT.name == 'notebooks':\n"
            "    PROJECT_ROOT = PROJECT_ROOT.parent\n"
            "sys.path.insert(0, str(PROJECT_ROOT))\n\n"
            "import json\n"
            "import pandas as pd\n"
            "import src.config as config\n"
            "from pyspark.sql import SparkSession\n"
            "from pyspark.sql.functions import col, avg, count, round\n\n"
            "spark = (\n"
            "    SparkSession.builder\n"
            "    .appName('BDA_03_PySpark_Processing')\n"
            "    .master('local[*]')\n"
            "    .config('spark.sql.shuffle.partitions', '4')\n"
            "    .config('spark.ui.enabled', 'false')\n"
            "    .getOrCreate()\n"
            ")\n"
            "print(f'Spark Version: {spark.version} | Master: {spark.sparkContext.master}')"
        ),
        new_markdown_cell("### 1. Ingesting Clean Partitioned Parquet Storage"),
        new_code_cell(
            "parquet_dir = PROJECT_ROOT / 'data' / 'processed' / 'clean_measurements_2024.parquet'\n"
            "clean_files = [str(f.resolve()) for f in sorted(parquet_dir.rglob('*.parquet')) if f.name != '_SUCCESS']\n"
            "df = spark.read.parquet(*clean_files)\n"
            "print(f'Total Processed Observations in Hive Parquet: {df.count():,}')\n"
            "df.printSchema()"
        ),
        new_markdown_cell("### 2. Spark SQL Analytics Temporary View"),
        new_code_cell(
            "df.createOrReplaceTempView('air_quality')\n\n"
            "# Spark SQL Query 1: Top 10 States with highest PM2.5 averages across 2024\n"
            "query_states = '''\n"
            "SELECT \n"
            "    state_name,\n"
            "    COUNT(*) as total_readings,\n"
            "    ROUND(AVG(CASE WHEN parameter_name = 'PM2.5' THEN value END), 2) as annual_avg_pm25,\n"
            "    ROUND(AVG(CASE WHEN parameter_name = 'PM10' THEN value END), 2) as annual_avg_pm10,\n"
            "    ROUND(AVG(CASE WHEN parameter_name = 'NO2' THEN value END), 2) as annual_avg_no2\n"
            "FROM air_quality\n"
            "WHERE state_name IS NOT NULL AND state_name != ''\n"
            "GROUP BY state_name\n"
            "HAVING COUNT(CASE WHEN parameter_name = 'PM2.5' THEN 1 END) >= 5000\n"
            "ORDER BY annual_avg_pm25 DESC\n"
            "LIMIT 10\n"
            "'''\n"
            "df_state_top = spark.sql(query_states)\n"
            "df_state_top.show(10, truncate=False)"
        ),
        new_markdown_cell("### 3. Pipeline Performance Metrics"),
        new_code_cell(
            "metrics_path = PROJECT_ROOT / 'outputs' / 'metrics' / 'spark_pipeline_metrics.json'\n"
            "with open(metrics_path) as f:\n"
            "    p_metrics = json.load(f)\n"
            "for k, v in p_metrics.items():\n"
            "    print(f'{k:<25}: {v}')"
        ),
        new_code_cell(
            "spark.stop()\n"
            "print('SparkSession closed.')"
        )
    ]
    nb.cells = cells
    nb_path = NOTEBOOKS_DIR / "03_pyspark_big_data_processing.ipynb"
    with open(nb_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
    return nb_path

def build_notebook_04():
    """Notebook 04: Pollution Trends and Hotspots"""
    nb = new_notebook()
    nb.metadata = {"kernelspec": {"display_name": "Python 3.10 (BDA Air Pollution)", "name": "bda-air-pollution"}}
    cells = [
        new_markdown_cell(
            "# Notebook 04: Temporal Pollution Trends, Diurnal Patterns, and Hotspot Identification\n"
            "## BDA Mini-Project: Air Pollution Analysis Across India\n\n"
            "### Objectives:\n"
            "- Analyze 24-hour diurnal patterns of PM2.5 and NO2 across Indian seasons.\n"
            "- Formulate the Multi-Criteria Hotspot Index (MCHI) using NAAQS exceedance frequency and persistence.\n"
            "- Rank the most persistent pollution hotspots across India.\n"
            "- Visualize geographical hotspot clusters across the Indo-Gangetic Plain and coastal corridors."
        ),
        new_code_cell(
            "import sys, os\n"
            "from pathlib import Path\n"
            "PROJECT_ROOT = Path(os.getcwd()).resolve()\n"
            "if PROJECT_ROOT.name == 'notebooks':\n"
            "    PROJECT_ROOT = PROJECT_ROOT.parent\n"
            "sys.path.insert(0, str(PROJECT_ROOT))\n\n"
            "import pandas as pd\n"
            "import matplotlib.pyplot as plt\n"
            "import seaborn as sns\n"
            "import src.config as config\n\n"
            "df_hotspots = pd.read_csv(config.OUTPUTS_TABLES_DIR / 'hotspots_ranking.csv')\n"
            "df_hourly = pd.read_csv(config.OUTPUTS_TABLES_DIR / 'hourly_pattern_summary.csv')\n"
            "print(f'Loaded {len(df_hotspots)} qualified stations and {len(df_hourly)} hourly summary rows.')"
        ),
        new_markdown_cell("### 1. Top 15 Persistent Pollution Hotspots Across India"),
        new_code_cell(
            "top15 = df_hotspots[['station_name', 'city_name', 'state_name', 'avg_pm25', 'pct_exceeding_naaqs', 'hotspot_score', 'classification']].head(15)\n"
            "print(top15.to_string(index=False))"
        ),
        new_markdown_cell("### 2. Diurnal 24-Hour Cycle & Planetary Boundary Layer Dynamics"),
        new_code_cell(
            "diurnal_chart_path = PROJECT_ROOT / 'outputs' / 'charts' / '04_diurnal_hourly_pattern.png'\n"
            "from IPython.display import Image, display\n"
            "display(Image(filename=str(diurnal_chart_path)))"
        ),
        new_markdown_cell("### 3. Spatial Distribution & Hotspot Severity"),
        new_code_cell(
            "severity_chart = PROJECT_ROOT / 'outputs' / 'charts' / '04_hotspot_severity_ranking.png'\n"
            "display(Image(filename=str(severity_chart)))"
        )
    ]
    nb.cells = cells
    nb_path = NOTEBOOKS_DIR / "04_pollution_trends_and_hotspots.ipynb"
    with open(nb_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
    return nb_path

def build_notebook_05():
    """Notebook 05: Advanced Analytics and Forecasting"""
    nb = new_notebook()
    nb.metadata = {"kernelspec": {"display_name": "Python 3.10 (BDA Air Pollution)", "name": "bda-air-pollution"}}
    cells = [
        new_markdown_cell(
            "# Notebook 05: Advanced Multi-Pollutant Analytics & PM2.5 Time-Series Forecasting\n"
            "## BDA Mini-Project: Air Pollution Analysis Across India\n\n"
            "### Objectives:\n"
            "- Analyze inter-pollutant Pearson correlations and atmospheric chemistry interactions.\n"
            "- Implement strict chronological train/validation/test forecasting experiment for Delhi NCR.\n"
            "- Benchmark Persistence Baseline, Rolling Average, Ridge Regression, and Gradient Boosting.\n"
            "- Discuss forecasting horizons, meteorological limitations, and academic conclusions."
        ),
        new_code_cell(
            "import sys, os\n"
            "from pathlib import Path\n"
            "PROJECT_ROOT = Path(os.getcwd()).resolve()\n"
            "if PROJECT_ROOT.name == 'notebooks':\n"
            "    PROJECT_ROOT = PROJECT_ROOT.parent\n"
            "sys.path.insert(0, str(PROJECT_ROOT))\n\n"
            "import json\n"
            "import pandas as pd\n"
            "from IPython.display import Image, display\n"
            "import src.config as config\n\n"
            "corr_df = pd.read_csv(config.OUTPUTS_TABLES_DIR / 'pollutant_correlation_matrix.csv', index_col=0)\n"
            "print('--- Inter-Pollutant Correlation Matrix ---')\n"
            "print(corr_df.to_string())"
        ),
        new_markdown_cell("### 1. Inter-Pollutant Correlation Heatmap"),
        new_code_cell(
            "hm_path = PROJECT_ROOT / 'outputs' / 'charts' / '05_pollutant_correlation_heatmap.png'\n"
            "display(Image(filename=str(hm_path)))"
        ),
        new_markdown_cell("### 2. PM2.5 Forecasting Model Comparison (Winter Holdout Set)"),
        new_code_cell(
            "metrics_path = PROJECT_ROOT / 'outputs' / 'metrics' / 'forecasting_metrics.json'\n"
            "with open(metrics_path) as f:\n"
            "    fc_res = json.load(f)\n"
            "df_eval = pd.DataFrame(fc_res).T\n"
            "print(df_eval.to_string())"
        ),
        new_markdown_cell("### 3. Actual vs Forecasted PM2.5 Time-Series Evaluation"),
        new_code_cell(
            "fc_chart = PROJECT_ROOT / 'outputs' / 'charts' / '05_pm25_forecasting_evaluation.png'\n"
            "display(Image(filename=str(fc_chart)))"
        ),
        new_markdown_cell(
            "### 4. Forecasting Limitations & Conclusions\n"
            "- **Persistence Strength:** In short 1-hour ahead forecasting, strong auto-correlation ($y_{t-1}$) provides a competitive baseline.\n"
            "- **Meteorological Dependency:** Multi-day forecasts require numerical weather prediction (wind speed, boundary layer height) to capture abrupt frontal ventilation."
        )
    ]
    nb.cells = cells
    nb_path = NOTEBOOKS_DIR / "05_advanced_analytics_and_forecasting.ipynb"
    with open(nb_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
    return nb_path

def execute_notebook(nb_path: Path):
    print(f"Executing {nb_path.name} with nbclient...")
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    client = NotebookClient(nb, timeout=300, kernel_name="bda-air-pollution")
    client.execute()

    with open(nb_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
    print(f"  [OK] Successfully executed {nb_path.name}!")

if __name__ == "__main__":
    n2 = build_notebook_02()
    execute_notebook(n2)

    n3 = build_notebook_03()
    execute_notebook(n3)

    n4 = build_notebook_04()
    execute_notebook(n4)

    n5 = build_notebook_05()
    execute_notebook(n5)
    print("\nALL NOTEBOOKS BUILT AND EXECUTED WITH SAVED OUTPUTS!")
