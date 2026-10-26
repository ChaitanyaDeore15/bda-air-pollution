"""
Verification script for BDA Project environment.
Checks Python, Java, SparkSession, PySpark DataFrames, dependencies, and XKDR API.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Initialize project config, Java and PySpark settings
import src.config

def check_system():
    print("=" * 60)
    print("1. SYSTEM & PYTHON ENVIRONMENT")
    print("=" * 60)
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    
    # Check Java
    print("\n" + "=" * 60)
    print("2. JAVA ENVIRONMENT")
    print("=" * 60)
    java_home = os.environ.get("JAVA_HOME", "NOT SET")
    print(f"JAVA_HOME: {java_home}")
    try:
        java_proc = subprocess.run(
            ["java", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print("Java Version Output:")
        print(java_proc.stderr.strip() or java_proc.stdout.strip())
    except Exception as e:
        print(f"ERROR: Java is not available on PATH: {e}")
        return False
    return True

def check_dependencies():
    print("\n" + "=" * 60)
    print("3. DEPENDENCY IMPORTS")
    print("=" * 60)
    packages = [
        "dotenv",
        "requests",
        "pyspark",
        "pandas",
        "pyarrow",
        "streamlit",
        "plotly",
        "matplotlib",
        "seaborn",
        "sklearn",
        "pytest",
    ]
    all_ok = True
    for pkg in packages:
        try:
            mod = __import__(pkg)
            version = getattr(mod, "__version__", "installed")
            print(f"  [OK] {pkg:<15} : {version}")
        except ImportError as e:
            print(f"  [FAIL] {pkg:<13} : {e}")
            all_ok = False
    return all_ok

def check_spark():
    print("\n" + "=" * 60)
    print("4. PYSPARK & SPARK SESSION TEST")
    print("=" * 60)
    try:
        import src.config  # Configures JAVA_HOME and PYSPARK_PYTHON
        from pyspark.sql import SparkSession
        from pyspark.sql.functions import col, avg

        # If on Windows, ensure hadoop home or winutils warning is handled gracefully
        spark = (
            SparkSession.builder
            .appName("BDA_Env_Verification")
            .master("local[2]")
            .config("spark.sql.shuffle.partitions", "2")
            .config("spark.ui.enabled", "false")
            .getOrCreate()
        )
        
        print(f"  [OK] SparkSession successfully created!")
        print(f"       Spark Version: {spark.version}")
        print(f"       Master: {spark.sparkContext.master}")

        # Test DataFrame operations
        test_data = [
            ("Delhi", "PM2.5", 142.5),
            ("Delhi", "PM2.5", 158.0),
            ("Mumbai", "PM2.5", 64.2),
            ("Mumbai", "PM2.5", 72.8),
            ("Bengaluru", "PM2.5", 38.5),
        ]
        df = spark.createDataFrame(test_data, ["City", "Pollutant", "Concentration"])
        print("\n  Sample Spark DataFrame created:")
        df.show()

        agg_df = df.groupBy("City").agg(avg("Concentration").alias("Avg_Concentration"))
        print("  Spark Aggregation Results:")
        agg_df.show()

        spark.stop()
        print("  [OK] SparkSession stopped cleanly.")
        return True
    except Exception as e:
        print(f"  [FAIL] Spark verification failed: {e}")
        return False

def check_api():
    print("\n" + "=" * 60)
    print("5. XKDR API CONNECTIVITY TEST")
    print("=" * 60)
    try:
        from src.api_client import XKDRAPIClient
        client = XKDRAPIClient()
        meta = client.get_meta()
        print("  [OK] Successfully authenticated with XKDR Air Quality API!")
        print(f"       Dataset Title / Schema: {list(meta.keys())}")
        if "user" in meta:
            print(f"       User tier / info: {meta['user']}")
        if "months" in meta:
            print(f"       Covered months count: {len(meta['months'])}")
            print(f"       Sample months: {meta['months'][:5]} ... {meta['months'][-3:]}")
        return True
    except Exception as e:
        print(f"  [FAIL] XKDR API test failed: {e}")
        return False

if __name__ == "__main__":
    s1 = check_system()
    s2 = check_dependencies()
    s3 = check_spark() if s2 else False
    s4 = check_api()
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"  System & Java       : {'PASS' if s1 else 'FAIL'}")
    print(f"  Dependencies        : {'PASS' if s2 else 'FAIL'}")
    print(f"  PySpark Execution   : {'PASS' if s3 else 'FAIL'}")
    print(f"  XKDR API Connection : {'PASS' if s4 else 'FAIL'}")
    print("=" * 60)
