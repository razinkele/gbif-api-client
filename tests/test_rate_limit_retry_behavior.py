import pandas as pd
import responses

from apis import OBISAPI


@responses.activate
def test_obis_retries_on_429_then_success():
    api = OBISAPI()
    url = api.base_url.rstrip("/") + "/occurrence"

    # Add two 429 responses, then a 200 with JSON payload
    responses.add(responses.GET, url, status=429)
    responses.add(responses.GET, url, status=429)
    sample = {"results": [{"species": "Salmo salar"}]}
    responses.add(responses.GET, url, json=sample, status=200)

    df = api.get_obis_records(["Salmo salar"])

    # Should have retried and eventually succeeded
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.iloc[0]["species"] == "Salmo salar"

    # Confirm that multiple calls were made (>=3)
    assert len(responses.calls) >= 3
