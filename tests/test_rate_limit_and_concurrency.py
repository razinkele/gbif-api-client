import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests

from apis import OBISAPI
from apis.base_api import BaseMarineAPI


def test_retry_adapter_includes_429():
    class Dummy(BaseMarineAPI):
        def get_taxa(self, *args, **kwargs):
            return []

    d = Dummy("https://example.org/")
    adapter = d.session.adapters.get("https://")
    assert adapter is not None
    # adapter.max_retries is a Retry instance when configured
    retries = getattr(adapter, "max_retries", None)
    assert retries is not None
    # Ensure status_forcelist includes 429
    status_forcelist = getattr(retries, "status_forcelist", None)
    assert status_forcelist is not None
    assert 429 in status_forcelist


def test_fallback_on_session_exception(monkeypatch):
    api = OBISAPI()

    def raise_request(*args, **kwargs):
        raise requests.RequestException("simulated connection error")

    monkeypatch.setattr(api.session, "request", raise_request)

    df = api.get_obis_records(["Any species"])
    # Should have fallen back to mock data
    assert isinstance(df, pd.DataFrame)
    assert not df.empty


def test_concurrent_obis_calls(monkeypatch):
    api = OBISAPI()

    # Patch _handle_response to simulate a slow but valid response
    def slow_handle_response(response):
        # simulate some processing delay
        time.sleep(0.05)
        return {"results": [{"species": response}]}

    # Patch _make_request to return the name (so handler can use it)
    def fake_make_request(endpoint, method="GET", params=None, data=None):
        # return the scientific name back via params
        return params.get("scientificname") if params else "unknown"

    monkeypatch.setattr(api, "_handle_response", slow_handle_response)
    monkeypatch.setattr(api, "_make_request", fake_make_request)

    inputs = [
        [{"latitude": 58.0, "longitude": 11.0}],
        [{"latitude": 59.0, "longitude": 12.0}],
        [{"latitude": 60.0, "longitude": 13.0}],
    ]

    # Submit concurrent lookup tasks
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = [ex.submit(api.lookup_xy, coords) for coords in inputs]
        results = []
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)

    # Expect a DataFrame result for each concurrent call
    assert len(results) == len(inputs)
    for df in results:
        assert isinstance(df, pd.DataFrame)
