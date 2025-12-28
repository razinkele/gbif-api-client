import pandas as pd
import responses

from apis import OBISAPI


@responses.activate
def test_get_obis_records_success():
    api = OBISAPI()
    url = api.base_url.rstrip("/") + "/occurrence"

    sample = {
        "results": [{"species": "Salmo salar", "longitude": 11.0, "latitude": 58.0}]
    }
    responses.add(responses.GET, url, json=sample, status=200)

    df = api.get_obis_records(["Salmo%20salar"])
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.iloc[0]["species"] == "Salmo salar"


@responses.activate
def test_get_obis_records_fallback():
    api = OBISAPI()
    url = api.base_url.rstrip("/") + "/occurrence"

    # Simulate server error
    responses.add(responses.GET, url, status=500)

    df = api.get_obis_records(["Nobody"])
    # Should fall back to mock data and not raise
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
