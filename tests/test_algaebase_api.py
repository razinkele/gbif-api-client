import pandas as pd
import responses

from apis import AlgaeBaseAPI


@responses.activate
def test_match_algaebase_taxa_success():
    api = AlgaeBaseAPI()
    url = api.base_url.rstrip("/") + "/search"

    sample = [{"name": "Fucus vesiculosus", "genus": "Fucus"}]
    responses.add(responses.GET, url, json=sample, status=200)

    df = api.match_algaebase_taxa(["Fucus"])
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.iloc[0]["name"] == "Fucus vesiculosus"


@responses.activate
def test_match_algaebase_taxa_fallback_on_error():
    api = AlgaeBaseAPI()
    url = api.base_url.rstrip("/") + "/search"

    # Simulate server error
    responses.add(responses.GET, url, status=500)

    # Should use fallback mock data and not raise
    df = api.match_algaebase_taxa(["Nonexistent sp."])
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "name" in df.columns
