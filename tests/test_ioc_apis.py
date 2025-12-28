import pandas as pd
import responses

from apis import IOCHABAPI, IOCToxinsAPI


@responses.activate
def test_get_hab_list_success():
    api = IOCHABAPI()
    url = api.base_url.rstrip("/") + "/list"
    sample = [{"species": "Alexandrium catenella"}]
    responses.add(responses.GET, url, json=sample, status=200)

    df = api.get_hab_list()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty


@responses.activate
def test_get_hab_list_fallback():
    api = IOCHABAPI()
    url = api.base_url.rstrip("/") + "/list"
    responses.add(responses.GET, url, status=500)

    df = api.get_hab_list()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty


@responses.activate
def test_get_toxin_list_success():
    api = IOCToxinsAPI()
    url = api.base_url.rstrip("/") + "/toxins"
    sample = [{"toxin": "Saxitoxin"}]
    responses.add(responses.GET, url, json=sample, status=200)

    df = api.get_toxin_list()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty


@responses.activate
def test_get_toxin_list_fallback():
    api = IOCToxinsAPI()
    url = api.base_url.rstrip("/") + "/toxins"
    responses.add(responses.GET, url, status=500)

    df = api.get_toxin_list()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
