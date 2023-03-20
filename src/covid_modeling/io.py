import os
from datetime import datetime

import dateutil.relativedelta
import numpy as np
import pandas as pd


class DataLoader:
    """
    Offers convenience functions for loading a defined set of patients and encounters data.

    """

    def __init__(self, data_dir):
        """
        :data_dir - The directory in which the expected CSV files are located.
        """
        self.data_dir = data_dir
        if not os.path.exists(data_dir):
            raise ValueError(f"Directory '{data_dir}' does not exist.")
        self.pdf = None
        self.edf = None
        self.hdf = None

        self._load_data()
        self._process_data()

    def _load_data(self):
        self.pdf = pd.read_csv(os.path.join(self.data_dir, "patients.csv"))
        self.edf = pd.read_csv(os.path.join(self.data_dir, "encounters.csv"))

    def _process_data(self):
        """
        Add additional columns to make the raw dataframes easier to work with.
        """
        # patient datetimes
        self.pdf["BIRTH"] = self.pdf.BIRTHDATE.map(lambda date_str: datetime.strptime(date_str, "%Y-%m-%d"))
        self.pdf["DEATH"] = self.pdf.DEATHDATE.map(
            lambda date_str: datetime.strptime(date_str, "%Y-%m-%d") if pd.notna(date_str) else np.nan,
        )
        self.pdf["LIFESPAN"] = self.pdf.DEATH - self.pdf.BIRTH

        # encounter datetimes
        self.edf["STARTDATE"] = self.edf.START.map(lambda date_str: datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ"))
        self.edf["STOPDATE"] = self.edf.STOP.map(lambda date_str: datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ"))

    def get_covid_hospitalizations_dataframe(self):
        """
        :returns The COVID-19 hospitalizations data, computing it from the raw data if necessary.
        """
        if self.hdf is None:
            self._compute_covid_hospitalizations_dataframe()
        return self.hdf

    def _compute_covid_hospitalizations_dataframe(self):
        """
        Note: 'magic numbers' in the implementation are explained and produced in the `DataExploration` notebook.
        """
        covid_code = 840539006
        death_cert_code = 308646001
        nonhospitalization_codes = [310061009, 56876005, 183495009, 305411003, 67799006, 185389009]
        covid_patients = self.edf.PATIENT[
            (self.edf.REASONCODE == covid_code) & (self.edf.ENCOUNTERCLASS == "inpatient")
        ]
        sdf = self.edf[
            (self.edf.PATIENT.isin(covid_patients)) & (self.edf.STARTDATE > datetime.strptime("2020-01-01", "%Y-%m-%d"))
        ]
        TOLERANCE = dateutil.relativedelta.relativedelta(days=1)

        hospitalizations = []
        for patient, group in sdf.groupby("PATIENT"):
            group = group.sort_values(by="STARTDATE")
            curr_start = None
            curr_stop = None
            is_covid_death = False
            is_covid_hospitalization = False
            organizations = []
            providers = []
            for encounter in group.itertuples():
                if encounter.ENCOUNTERCLASS == "inpatient" and encounter.CODE not in nonhospitalization_codes:
                    organizations.append(encounter.ORGANIZATION)
                    providers.append(encounter.PROVIDER)
                    if encounter.REASONCODE == covid_code:
                        is_covid_hospitalization = True
                    if curr_start is None:
                        curr_start = encounter.STARTDATE
                        curr_stop = encounter.STOPDATE
                    elif encounter.STOPDATE > curr_stop and encounter.STOPDATE < curr_stop + TOLERANCE:
                        curr_stop = encounter.STOPDATE
                    elif curr_stop > curr_stop + TOLERANCE:
                        # new hospitalization
                        org_counts = pd.Series(organizations).value_counts()
                        provider_counts = pd.Series(providers).value_counts()
                        hospitalizations.append(
                            {
                                "patient": patient,
                                "startdate": curr_start,
                                "stopdate": curr_stop,
                                "is_covid_hospitalization": is_covid_hospitalization,
                                "is_covid_death": is_covid_death,
                                "n_organizations": len(org_counts),
                                "leading_organization": org_counts.index[0],
                                "n_providers": len(provider_counts),
                                "leading_provider": provider_counts.index[0],
                            },
                        )
                        curr_start = encounter.STARTDATE
                        curr_stop = encounter.STOPDATE
                        is_covid_death = False
                        is_covid_hospitalization = encounter.REASONCODE == covid_code
                        organizations = [encounter.ORGANIZATION]
                        providers = [encounter.PROVIDER]
                elif encounter.CODE == death_cert_code and encounter.REASONCODE == covid_code:
                    assert curr_start is not None
                    is_covid_death = True
            if curr_start is not None:
                org_counts = pd.Series(organizations).value_counts()
                provider_counts = pd.Series(providers).value_counts()
                hospitalizations.append(
                    {
                        "patient": patient,
                        "startdate": curr_start,
                        "stopdate": curr_stop,
                        "is_covid_hospitalization": is_covid_hospitalization,
                        "is_covid_death": is_covid_death,
                        "n_organizations": len(org_counts),
                        "leading_organization": org_counts.index[0],
                        "n_providers": len(provider_counts),
                        "leading_provider": provider_counts.index[0],
                    },
                )
        hdf = pd.DataFrame(hospitalizations)
        hdf["duration"] = hdf.stopdate - hdf.startdate

        # merge in the patient data
        # and drop some of the extraneous columns
        hdf = (
            hdf.merge(
                self.pdf[["Id", "BIRTH", "GENDER", "RACE"]],
                how="left",
                left_on="patient",
                right_on="Id",
            )
            .drop(
                columns=["Id", "n_providers", "n_organizations", "leading_organization"],
            )
            .rename(
                columns={"BIRTH": "birthdate", "GENDER": "gender", "RACE": "race"},
            )
        )

        # compute age at time of hospitalization
        hdf["age"] = hdf.startdate - hdf.birthdate

        # assign the new dataframe
        self.hdf = hdf
