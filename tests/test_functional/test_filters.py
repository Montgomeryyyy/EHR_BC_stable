import unittest

from corebehrt.modules.preparation.dataset import PatientData
from corebehrt.functional.preparation.filter import (
    exclude_short_sequences,
    censor_patient,
    filter_rows_by_regex,
)
import pandas as pd
from datetime import datetime


class TestExcludeShortSequences(unittest.TestCase):
    def test_exclude_short_sequences_basic(self):
        # Create some dummy PatientData objects
        p1 = PatientData(
            pid=1,
            concepts=[1, 2, 3],
            abspos=[10.0, 11.0, 12.0],
            segments=[0, 1, 1],
            ages=[40.0, 41.0, 42.0],
        )
        p2 = PatientData(
            pid=2,
            concepts=[1, 2],
            abspos=[5.0, 6.0],
            segments=[0, 0],
            ages=[30.0, 31.0],
        )
        patients = [p1, p2]

        # Only keep patients with concepts >= 3
        min_len = 3
        result = exclude_short_sequences(patients, min_len)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].pid, 1)

    def test_exclude_short_sequences_empty(self):
        # No patients at all
        patients = []
        result = exclude_short_sequences(patients, min_len=2)
        self.assertEqual(len(result), 0)

    def test_exclude_short_sequences_edge_case(self):
        # Exactly matching the min_len
        p1 = PatientData(1, [1, 2], [10, 11], [0, 1], [40, 41])
        patients = [p1]
        result = exclude_short_sequences(patients, min_len=2)
        # p1 has concept length == min_len, so it should be included
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].pid, 1)


class TestCensorPatient(unittest.TestCase):
    def test_censor_patient_basic(self):
        # Setup a single patient
        p1 = PatientData(
            pid=1,
            concepts=[101, 102, 103],
            abspos=[1.0, 2.5, 4.0],
            segments=[0, 0, 1],
            ages=[30.0, 31.2, 32.1],
        )
        censor_dates = {1: 2.5}

        censored = censor_patient(p1, censor_dates)
        self.assertEqual(len(censored.concepts), 2)
        # We expect only abspos <= 2.5, so indexes 0 and 1 remain
        self.assertListEqual(censored.concepts, [101, 102])
        self.assertListEqual(censored.abspos, [1.0, 2.5])
        self.assertListEqual(censored.segments, [0, 0])
        self.assertListEqual(censored.ages, [30.0, 31.2])

    def test_censor_patient_no_events(self):
        # If everything is after the censor date, we get an empty list
        p1 = PatientData(
            pid=1,
            concepts=[101, 102],
            abspos=[5.0, 6.0],
            segments=[0, 1],
            ages=[30.0, 31.0],
        )
        censor_dates = {1: 2.0}

        censored = censor_patient(p1, censor_dates)
        self.assertEqual(len(censored.concepts), 0)
        self.assertEqual(len(censored.abspos), 0)
        self.assertEqual(len(censored.segments), 0)
        self.assertEqual(len(censored.ages), 0)

    def test_censor_patient_all_included(self):
        # If censor_date is large, everything is included
        p1 = PatientData(1, [101], [10.0], [1], [50.0])
        censor_dates = {1: 999.0}
        censored = censor_patient(p1, censor_dates)
        self.assertEqual(len(censored.concepts), 1)


class TestRegexFilter(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame(
            {
                "subject_id": [1, 1, 2, 3, 3, 3],
                "code": [
                    "DOB",
                    "DC521",
                    "MN001",
                    "PZZ3912",
                    "MA01",
                    "LAB_KOLESTEROL LDL;P",
                ],
                "time": [
                    datetime(1995, 5, 1),
                    datetime(2000, 5, 1),
                    datetime(2015, 7, 1),
                    datetime(2015, 7, 2),
                    datetime(2016, 8, 2),
                    datetime(2016, 8, 2),
                ],
            }
        )

    def test_positive_filter(self):
        md_regex = r"^(LAB_.*|P[A-Z].*)$"
        expected_md = ["DOB", "DC521", "MN001", "MA01"]
        md_df = filter_rows_by_regex(self.df, "code", md_regex)
        self.assertListEqual(md_df["code"].tolist(), expected_md)

    def test_negative_filter(self):
        non_md_regex = r"^(?!LAB_.*|P[A-Z].*).*$"
        expected_non_md = ["PZZ3912", "LAB_KOLESTEROL LDL;P"]
        non_md_df = filter_rows_by_regex(self.df, "code", non_md_regex)
        self.assertListEqual(non_md_df["code"].tolist(), expected_non_md)

    def test_empty_filter(self):
        all_regex = ".*"
        empty_df = filter_rows_by_regex(self.df, "code", all_regex)
        self.assertEqual(empty_df.shape[0], 0)


if __name__ == "__main__":
    unittest.main()
