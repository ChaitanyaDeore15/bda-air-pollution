"""
XKDR Forum India Air Quality Database API Client.
Provides secure, resilient, and documented access to historical air quality observations.
"""

import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config import (
    get_api_key,
    META_ENDPOINT,
    STATIONS_ENDPOINT,
    PARAMETERS_ENDPOINT,
    MEASUREMENTS_ENDPOINT,
    FILES_ENDPOINT,
    DATA_RAW_DIR,
    DATA_SAMPLE_DIR,
    DATA_METADATA_DIR,
    OUTPUTS_LOGS_DIR,
)

# Set up logging (never log secret tokens)
LOG_FILE = OUTPUTS_LOGS_DIR / "api_client.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("XKDRAPIClient")


class XKDRAPIClient:
    """
    Client for interacting with the XKDR Forum India Air Quality Database API (v1).
    Documentation: https://airquality.xkdr.org/v1/docs
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initializes the client. Uses XKDR_API_KEY from environment if not provided.
        """
        self.api_key = api_key or get_api_key()
        self.session = self._create_resilient_session()

    def _create_resilient_session(self) -> requests.Session:
        """
        Configures requests Session with retry strategy for transient errors (429, 500, 502, 503, 504).
        """
        session = requests.Session()
        retry_strategy = Retry(
            total=4,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "BDA-AirPollution-Project/1.0",
        })
        return session

    def _request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 45,
        stream: bool = False,
    ) -> requests.Response:
        """
        Executes an HTTP GET request with error sanitization to protect API credentials.
        """
        try:
            response = self.session.get(url, params=params, timeout=timeout, stream=stream)
            if response.status_code == 401:
                logger.error("Authentication failed (HTTP 401). Please verify your XKDR API key.")
                response.raise_for_status()
            elif response.status_code == 403:
                logger.error("Access forbidden (HTTP 403). Requested resource is outside your tier/permission limits.")
                response.raise_for_status()
            elif response.status_code == 429:
                logger.warning("Rate limit hit (HTTP 429). Exponential backoff triggered.")
                response.raise_for_status()
            elif not response.ok:
                logger.error(f"HTTP request error: {response.status_code} for endpoint {url.split('?')[0]}")
                response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            # Mask API key if accidentally leaked in URL or error strings
            safe_msg = str(e).replace(self.api_key, "[REDACTED_API_KEY]")
            logger.error(f"Network error during request: {safe_msg}")
            raise RuntimeError(f"XKDR API request failed: {safe_msg}") from None

    def get_meta(self) -> Dict[str, Any]:
        """
        Retrieves metadata regarding dataset status, available months, row caps, and user tier.
        Endpoint: GET /v1/meta
        """
        logger.info("Fetching dataset metadata from /v1/meta...")
        resp = self._request(META_ENDPOINT)
        return resp.json()

    def get_stations(
        self,
        source: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        q: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Lists monitoring stations with coordinates, dates, and monitored parameters.
        Endpoint: GET /v1/stations
        """
        params = {}
        if source:
            params["source"] = source
        if state:
            params["state"] = state
        if city:
            params["city"] = city
        if q:
            params["q"] = q

        logger.info(f"Fetching stations with params: {params}...")
        resp = self._request(STATIONS_ENDPOINT, params=params)
        return resp.json()

    def get_parameters(self) -> List[Dict[str, Any]]:
        """
        Lists tracked pollutants, units, and active station counts.
        Endpoint: GET /v1/parameters
        """
        logger.info("Fetching parameters from /v1/parameters...")
        resp = self._request(PARAMETERS_ENDPOINT)
        return resp.json()

    def get_measurements(
        self,
        station: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        parameter: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        agg: Optional[str] = None,
        fmt: str = "json",
        limit: Optional[int] = None,
    ) -> Union[List[Dict[str, Any]], bytes]:
        """
        Queries measurement records.
        Endpoint: GET /v1/measurements
        Supported formats: 'json', 'csv', 'parquet'
        """
        params: Dict[str, Any] = {"format": fmt}
        if station:
            params["station"] = station
        if city:
            params["city"] = city
        if state:
            params["state"] = state
        if parameter:
            params["parameter"] = parameter
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if agg:
            params["agg"] = agg
        if limit:
            params["limit"] = limit

        logger.info(f"Fetching measurements with params={params}...")
        resp = self._request(MEASUREMENTS_ENDPOINT, params=params)
        if fmt == "json":
            return resp.json()
        return resp.content

    def get_files(self) -> List[Dict[str, Any]]:
        """
        Lists raw underlying bulk Parquet files.
        Endpoint: GET /v1/files
        """
        logger.info("Fetching bulk files list from /v1/files...")
        resp = self._request(FILES_ENDPOINT)
        return resp.json()

    def download_bulk_file(
        self,
        file_url: str,
        destination_path: Path,
        chunk_size: int = 1024 * 1024,
    ) -> Path:
        """
        Downloads a bulk Parquet archive with streaming and integrity reporting.
        """
        destination_path = Path(destination_path)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Downloading {file_url} -> {destination_path}...")
        start_time = time.time()

        resp = self._request(file_url, stream=True, timeout=120)
        total_bytes = 0
        with open(destination_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    total_bytes += len(chunk)

        elapsed = time.time() - start_time
        mb = total_bytes / (1024 * 1024)
        logger.info(f"Successfully downloaded {mb:.2f} MB in {elapsed:.1f}s ({mb / max(elapsed, 0.001):.2f} MB/s)")
        return destination_path
