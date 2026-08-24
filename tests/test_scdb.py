"""Tests for SCDB matching.

SCDB and CourtListener write case names in different registers, so the join
must survive: all-caps, 'et al.' both before and after the 'v.', spelled-out
official titles, and 'DOING BUSINESS AS' tails.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from uslegalqa.scdb import name_key, norm_citation, ISSUE_AREAS


@pytest.mark.parametrize("cite,expected", [
    ("544 U.S. 431", "544-431"),
    ("576 U. S. 644", "576-644"),
    ("329 U.S. 1", "329-1"),
    ("1 US 2", "1-2"),
    (None, None),
    ("", None),
    ("no citation here", None),
])
def test_citation_normalisation(cite, expected):
    assert norm_citation(cite) == expected


@pytest.mark.parametrize("scdb_name,cl_name", [
    ("HALLIBURTON OIL WELL CEMENTING CO. v. WALKER et al., DOING BUSINESS AS DEPTHOGRAPH CO.",
     "Halliburton Oil Well Cementing Co. v. Walker"),
    ("BATES et al. v. DOW AGROSCIENCES LLC", "Bates v. Dow Agrosciences LLC"),
    ("GONZALES, ATTORNEY GENERAL, et al. v. RAICH et al.", "Gonzales v. Raich"),
    ("KELO et al. v. CITY OF NEW LONDON et al.", "Kelo v. New London"),
    ("MERCK KGaA v. INTEGRA LIFESCIENCES I, LTD., et al.",
     "Merck Kgaa v. Integra Lifesciences I, Ltd."),
])
def test_matching_names_produce_same_key(scdb_name, cl_name):
    assert name_key(scdb_name) == name_key(cl_name)


@pytest.mark.parametrize("a,b", [
    ("Alpha v. Beta", "Gamma v. Delta"),
    ("Smith v. Jones", "Smith v. Williams"),
    ("Miller v. Alabama", "Miller v. California"),
])
def test_different_cases_produce_different_keys(a, b):
    assert name_key(a) != name_key(b)


def test_empty_name_is_empty_key():
    assert name_key("") == ""
    assert name_key(None) == ""


def test_issue_area_codes_cover_scdb_range():
    assert set(ISSUE_AREAS) == {str(i) for i in range(1, 15)}
    assert ISSUE_AREAS["1"] == "criminal_procedure"
    assert ISSUE_AREAS["8"] == "economic_activity"
