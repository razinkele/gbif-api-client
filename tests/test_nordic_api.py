import pandas as pd
import responses

from apis import NordicMicroalgaeAPI


@responses.activate
def test_get_nordic_taxa_success():
    api = NordicMicroalgaeAPI()
    url = api.base_url.rstrip("/") + "/taxa"
    sample = [{"name": "Aphanizomenon flos-aquae"}]
    responses.add(responses.GET, url, json=sample, status=200)

    df = api.get_nordic_microalgae_taxa()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.iloc[0]["name"] == "Aphanizomenon flos-aquae"


@responses.activate
def test_get_nordic_taxa_fallback():
    api = NordicMicroalgaeAPI()
    url = api.base_url.rstrip("/") + "/taxa"
    responses.add(responses.GET, url, status=500)

    df = api.get_nordic_microalgae_taxa()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty


@responses.activate
def test_get_nua_harmfulness_success():
    api = NordicMicroalgaeAPI()
    taxon_id = 123
    url = api.base_url.rstrip("/") + f"/taxa/{taxon_id}/harmfulness"
    sample = {"harmfulness": "Toxic"}
    responses.add(responses.GET, url, json=sample, status=200)

    df = api.get_nua_harmfulness([taxon_id])
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.iloc[0]["taxon_id"] == taxon_id
