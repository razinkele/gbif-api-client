import pandas as pd
import responses

from apis import WoRMSAPI


@responses.activate
def test_get_worms_records_success():
    api = WoRMSAPI()
    name = "Fucus%20vesiculosus"
    url = api.base_url.rstrip("/") + f"/AphiaRecordsByName/{name}"

    sample = [{"AphiaID": 1, "scientificname": "Fucus vesiculosus"}]
    responses.add(responses.GET, url, json=sample, status=200)

    df = api.get_worms_records(["Fucus%20vesiculosus"])
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.iloc[0]["scientificname"] == "Fucus vesiculosus"


@responses.activate
def test_get_worms_records_fallback():
    api = WoRMSAPI()
    name = "Nobody"
    url = api.base_url.rstrip("/") + f"/AphiaRecordsByName/{name}"

    responses.add(responses.GET, url, status=404)

    df = api.get_worms_records(["Nobody"])
    # Should fall back to mock data and return DataFrame
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
