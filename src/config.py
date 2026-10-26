"""
Configuration and Environment Management Module.
Handles environment variables, API keys, paths, and Spark settings securely.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_SAMPLE_DIR = DATA_DIR / "sample"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_METADATA_DIR = DATA_DIR / "metadata"

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
OUTPUTS_CHARTS_DIR = OUTPUTS_DIR / "charts"
OUTPUTS_TABLES_DIR = OUTPUTS_DIR / "tables"
OUTPUTS_METRICS_DIR = OUTPUTS_DIR / "metrics"
OUTPUTS_LOGS_DIR = OUTPUTS_DIR / "logs"

# Ensure directories exist
for path in [
    DATA_RAW_DIR,
    DATA_SAMPLE_DIR,
    DATA_PROCESSED_DIR,
    DATA_METADATA_DIR,
    OUTPUTS_CHARTS_DIR,
    OUTPUTS_TABLES_DIR,
    OUTPUTS_METRICS_DIR,
    OUTPUTS_LOGS_DIR,
]:
    path.mkdir(parents=True, exist_ok=True)

# Load environment variables from .env file
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)

import sys
import ctypes

def get_short_path(path_str: str) -> str:
    """Converts a Windows path to an 8.3 short path without spaces."""
    if os.name == "nt":
        buf = ctypes.create_unicode_buffer(500)
        ret = ctypes.windll.kernel32.GetShortPathNameW(path_str, buf, 500)
        if ret > 0 and buf.value:
            return buf.value
    return path_str

# Automatic Java 21 detection if JAVA_HOME not explicitly set
if "JAVA_HOME" not in os.environ:
    potential_java = Path(r"C:\Program Files\Java\jdk-21")
    if potential_java.exists():
        os.environ["JAVA_HOME"] = str(potential_java)
        os.environ["PATH"] = f"{potential_java / 'bin'};{os.environ.get('PATH', '')}"

# Configure HADOOP_HOME for Windows Spark write operations
hadoop_dir = PROJECT_ROOT / "hadoop"
if hadoop_dir.exists():
    os.environ["HADOOP_HOME"] = get_short_path(str(hadoop_dir))
    os.environ["PATH"] = f"{get_short_path(str(hadoop_dir / 'bin'))};{os.environ.get('PATH', '')}"

python_path = get_short_path(sys.executable)
os.environ["PYSPARK_PYTHON"] = python_path
os.environ["PYSPARK_DRIVER_PYTHON"] = python_path

def get_api_key() -> str:
    """
    Safely retrieves the XKDR API key from environment variables.
    Raises ValueError if missing or set to the placeholder.
    """
    api_key = os.getenv("XKDR_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "XKDR_API_KEY is missing! Please configure it in your .env file."
        )
    if api_key in ("PASTE_YOUR_REAL_API_KEY_HERE", "your_key_here"):
        raise ValueError(
            "XKDR_API_KEY is set to placeholder text. Please replace it with your valid key."
        )
    return api_key

# XKDR API Endpoints
API_BASE_URL = "https://airquality.xkdr.org"
META_ENDPOINT = f"{API_BASE_URL}/v1/meta"
STATIONS_ENDPOINT = f"{API_BASE_URL}/v1/stations"
PARAMETERS_ENDPOINT = f"{API_BASE_URL}/v1/parameters"
MEASUREMENTS_ENDPOINT = f"{API_BASE_URL}/v1/measurements"
FILES_ENDPOINT = f"{API_BASE_URL}/v1/files"

# Spark Configuration
SPARK_APP_NAME = "IndiaAirQualityBDA"
SPARK_MASTER = "local[*]"
SPARK_DRIVER_MEMORY = "4g"
SPARK_SQL_SHUFFLE_PARTITIONS = "8"

# National Ambient Air Quality Standards (NAAQS) India (24-Hour standards in ug/m3, CO in mg/m3)
NAAQS_THRESHOLDS_24H = {
    "pm25": 60.0,
    "pm10": 100.0,
    "no2": 80.0,
    "so2": 80.0,
    "co": 2.0,  # 8-hr standard mg/m3
    "o3": 100.0,  # 8-hr standard ug/m3
}
