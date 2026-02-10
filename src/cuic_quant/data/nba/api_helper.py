"""Rate-limited wrapper for nba_api endpoint calls."""

from __future__ import annotations

import logging
import time

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from cuic_quant.data.nba.constants import MAX_RETRIES, REQUEST_DELAY

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    reraise=True,
)
def _call_endpoint(endpoint_class: type, **kwargs) -> list[pd.DataFrame]:
    """Call an nba_api endpoint with retry logic."""
    instance = endpoint_class(**kwargs)
    return instance.get_data_frames()


def fetch_endpoint(
    endpoint_class: type,
    dataset_index: int = 0,
    **kwargs,
) -> pd.DataFrame:
    """Fetch data from an nba_api endpoint with rate limiting and retries.

    Args:
        endpoint_class: The nba_api endpoint class to call.
        dataset_index: Which DataFrame to return (endpoints return multiple).
        **kwargs: Arguments passed to the endpoint constructor.

    Returns:
        DataFrame from the endpoint, or empty DataFrame on failure.
    """
    time.sleep(REQUEST_DELAY)
    try:
        frames = _call_endpoint(endpoint_class, **kwargs)
        if frames and len(frames) > dataset_index:
            return frames[dataset_index]
        return pd.DataFrame()
    except Exception:
        logger.exception(
            "Failed to fetch %s with args %s",
            endpoint_class.__name__ if hasattr(endpoint_class, "__name__") else str(endpoint_class),
            kwargs,
        )
        return pd.DataFrame()
