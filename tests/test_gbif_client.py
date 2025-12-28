import pytest

from gbif_client import GBIFClient


def test_gbif_client_methods_return_defaults_when_pygbif_missing(monkeypatch):
    # Simulate pygbif missing by toggling the _HAS_PYGBIF flag
    monkeypatch.setattr("gbif_client._HAS_PYGBIF", False)
    client = GBIFClient()

    # search_species should return empty list
    assert client.search_species("Any species") == []

    # get_species_info should return None
    assert client.get_species_info(12345) is None

    # search_occurrences should return empty dict
    assert client.search_occurrences(taxon_key=1) == {}

    # get_occurrence_count should return 0
    assert client.get_occurrence_count(taxon_key=1) == 0

    # get_datasets should return []
    assert client.get_datasets() == []


@pytest.mark.parametrize("bad_name", ["", None])
def test_search_species_invalid_name_raises(bad_name):
    client = GBIFClient()
    with pytest.raises(ValueError):
        client.search_species(bad_name)
