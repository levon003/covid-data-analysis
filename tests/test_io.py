import pathlib

import pytest

import covid_modeling.io


def test_DataLoader(pytestconfig):
    with pytest.raises(ValueError):
        covid_modeling.io.DataLoader(pathlib.Path("fake_path"))

    test_data_dir = pytestconfig.rootpath / "tests" / "resources"
    dl = covid_modeling.io.DataLoader(test_data_dir)
    assert "LIFESPAN" in dl.pdf
    assert "STARTDATE" in dl.edf
    assert "STOPDATE" in dl.edf
    hdf = dl.get_covid_hospitalizations_dataframe()
    assert hdf is not None
