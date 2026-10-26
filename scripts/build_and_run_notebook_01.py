"""
Builds and executes notebooks/01_dataset_exploration.ipynb with real data outputs.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell
from nbclient import NotebookClient

NOTEBOOK_PATH = Path(__file__).resolve().parent.parent / "notebooks" / "01_dataset_exploration.ipynb"

def create_exploration_notebook():
    nb = new_notebook()
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3.10 (BDA Air Pollution)",
            "language": "python",
            "name": "bda-air-pollution"
        },
        "language_info": {
            "name": "python",
            "version": "3.10.11"
        }
    }

    cells = []

    # Cell 1: Markdown Title
    cells.append(new_markdown_cell(
        "# Notebook 01: Dataset Exploration & Schema Inspection\n"
        "## Analysis of Air Pollution Patterns and Hotspots Across India Using Apache Spark\n\n"
        "**Source:** XKDR Forum India Air Quality Database (`https://airquality.xkdr.org`)\n\n"
        "### Objectives:\n"
        "1. Inspect the official XKDR air quality schema and data dictionary.\n"
        "2. Initialize an optimized local Apache Spark session.\n"
        "3. Ingest real historical hourly observations (January 2024 sample of 4+ million records).\n"
        "4. Explore pollutant parameters, measurement units, and monitoring stations.\n"
        "5. Execute initial Spark SQL aggregations and produce exploratory visualizations."
    ))

    # Cell 2: Code Imports & Config
    cells.append(new_code_cell(
        "import sys\n"
        "import os\n"
        "from pathlib import Path\n\n"
        "# Ensure project root is in sys.path\n"
        "PROJECT_ROOT = Path(os.getcwd()).resolve()\n"
        "if PROJECT_ROOT.name == 'notebooks':\n"
        "    PROJECT_ROOT = PROJECT_ROOT.parent\n"
        "sys.path.insert(0, str(PROJECT_ROOT))\n\n"
        "import src.config as config\n"
        "import pandas as pd\n"
        "import matplotlib.pyplot as plt\n"
        "import seaborn as sns\n"
        "from pyspark.sql import SparkSession\n"
        "from pyspark.sql.functions import col, count, avg, min, max, stddev, round\n\n"
        "print('Dependencies loaded successfully!')\n"
        "print('Project Root:', PROJECT_ROOT)"
    ))

    # Cell 3: SparkSession Initialization
    cells.append(new_code_cell(
        "# Initialize SparkSession with optimized local settings\n"
        "spark = (\n"
        "    SparkSession.builder\n"
        "    .appName('BDA_01_Dataset_Exploration')\n"
        "    .master('local[*]')\n"
        "    .config('spark.sql.shuffle.partitions', '4')\n"
        "    .config('spark.driver.memory', '4g')\n"
        "    .config('spark.ui.enabled', 'false')\n"
        "    .getOrCreate()\n"
        ")\n\n"
        "print(f'SparkSession Active | Spark Version: {spark.version} | Master: {spark.sparkContext.master}')"
    ))

    # Cell 4: Load Real Data Sample & Metadata
    cells.append(new_markdown_cell(
        "### Ingesting Real Historical Measurements & Metadata\n"
        "We load the downloaded sample month (`measurements_2024_01.parquet`), monitoring stations (`stations.parquet`), and parameter definitions (`parameters.parquet`)."
    ))

    cells.append(new_code_cell(
        "sample_parquet_path = PROJECT_ROOT / 'data' / 'sample' / 'measurements_2024_01.parquet'\n"
        "stations_parquet_path = PROJECT_ROOT / 'data' / 'metadata' / 'stations.parquet'\n"
        "parameters_parquet_path = PROJECT_ROOT / 'data' / 'metadata' / 'parameters.parquet'\n\n"
        "df_measurements = spark.read.parquet(str(sample_parquet_path))\n"
        "df_stations = spark.read.parquet(str(stations_parquet_path))\n"
        "df_parameters = spark.read.parquet(str(parameters_parquet_path))\n\n"
        "total_records = df_measurements.count()\n"
        "print(f'Total Real Observations in Sample Month: {total_records:,}')\n"
        "print(f'Total Monitoring Stations in India: {df_stations.count():,}')\n"
        "print(f'Total Tracked Pollutants & Meteorological Parameters: {df_parameters.count():,}')"
    ))

    # Cell 5: Print Schema & Sample Records
    cells.append(new_markdown_cell("### Measurements Schema Inspection"))
    cells.append(new_code_cell(
        "print('--- Measurements Schema ---')\n"
        "df_measurements.printSchema()\n\n"
        "print('--- First 5 Real Observations ---')\n"
        "df_measurements.show(5, truncate=False)"
    ))

    # Cell 6: Pollutant Parameter Distribution
    cells.append(new_markdown_cell("### Observations Distribution Across Pollutants & Units"))
    cells.append(new_code_cell(
        "pollutant_dist = (\n"
        "    df_measurements.groupBy('parameter_name', 'unit')\n"
        "    .agg(count('*').alias('observation_count'),\n"
        "         round(avg('value'), 2).alias('mean_val'),\n"
        "         round(min('value'), 2).alias('min_val'),\n"
        "         round(max('value'), 2).alias('max_val'))\n"
        "    .orderBy(col('observation_count').desc())\n"
        ")\n"
        "pollutant_dist.show(15, truncate=False)"
    ))

    # Cell 7: City-Level Observation Counts & Top Polluted Cities for PM2.5
    cells.append(new_markdown_cell("### City-Level PM2.5 Analysis (January 2024 Sample)"))
    cells.append(new_code_cell(
        "# Register as Spark SQL temporary view\n"
        "df_measurements.createOrReplaceTempView('measurements')\n\n"
        "query = '''\n"
        "SELECT \n"
        "    city_name,\n"
        "    state_name,\n"
        "    COUNT(value) as valid_readings,\n"
        "    ROUND(AVG(value), 2) as avg_pm25,\n"
        "    ROUND(MIN(value), 2) as min_pm25,\n"
        "    ROUND(MAX(value), 2) as max_pm25\n"
        "FROM measurements\n"
        "WHERE parameter_name = 'PM2.5' AND value >= 0\n"
        "GROUP BY city_name, state_name\n"
        "HAVING COUNT(value) >= 500\n"
        "ORDER BY avg_pm25 DESC\n"
        "LIMIT 10\n"
        "'''\n"
        "top_cities_pm25 = spark.sql(query)\n"
        "top_cities_pm25.show(10, truncate=False)"
    ))

    # Cell 8: Exploratory Data Visualization
    cells.append(new_markdown_cell("### Exploratory Visualizations: Top 10 PM2.5 Cities in January 2024"))
    cells.append(new_code_cell(
        "top_cities_pd = top_cities_pm25.toPandas()\n\n"
        "plt.figure(figsize=(10, 5), dpi=100)\n"
        "sns.set_theme(style='whitegrid')\n"
        "ax = sns.barplot(\n"
        "    data=top_cities_pd,\n"
        "    x='avg_pm25',\n"
        "    y='city_name',\n"
        "    palette='Reds_r'\n"
        ")\n"
        "# Add NAAQS 24-hr threshold line (60 ug/m3)\n"
        "plt.axvline(60, color='blue', linestyle='--', linewidth=1.5, label='NAAQS Standard (60 µg/m³)')\n"
        "plt.title('Top 10 Cities with Highest Mean PM2.5 Concentration (January 2024)', fontsize=13, weight='bold')\n"
        "plt.xlabel('Average PM2.5 (µg/m³)', fontsize=11)\n"
        "plt.ylabel('City', fontsize=11)\n"
        "plt.legend(loc='lower right')\n"
        "plt.tight_layout()\n\n"
        "# Save chart to outputs directory\n"
        "chart_path = PROJECT_ROOT / 'outputs' / 'charts' / '01_top_pm25_cities_jan2024.png'\n"
        "plt.savefig(chart_path)\n"
        "plt.show()\n"
        "print(f'Chart saved to {chart_path}')"
    ))

    # Cell 9: Clean Shutdown
    cells.append(new_markdown_cell("### Conclusion & Spark Cleanup"))
    cells.append(new_code_cell(
        "spark.stop()\n"
        "print('SparkSession stopped cleanly.')"
    ))

    nb.cells = cells
    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
    print(f"Created notebook structure at {NOTEBOOK_PATH}")
    return nb

def execute_notebook():
    print("Executing notebook with nbclient...")
    with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    client = NotebookClient(nb, timeout=600, kernel_name="bda-air-pollution")
    client.execute()

    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
    print(f"Successfully executed and saved outputs to {NOTEBOOK_PATH}!")

if __name__ == "__main__":
    create_exploration_notebook()
    execute_notebook()
