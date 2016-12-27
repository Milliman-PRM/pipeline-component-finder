"""
### CODE OWNERS: Shea Parkes, Kyle Baird

### OBJECTIVE:
  Test the easily testible bits.

### DEVELOPER NOTES:
  Mutates the schema below for testing sanity.
"""
import logging
import json
from pathlib import Path

import pytest
import jsonschema

import component_finder

LOGGER = logging.getLogger(__name__)
PATH_TEST_CASES = Path(__file__).parent

# Hack in our desired testing names
component_finder.SCHEMA_RELEASE['definitions']['authorized_qrm_signers']['enum'] = [
    'dudley.doright@milliman.com',
    'moose@milliman.com',
    'squirrel@milliman.com',
]

# =============================================================================
# LIBRARIES, LOCATIONS, LITERALS, ETC. GO ABOVE HERE
# =============================================================================

def test_schema_success():
    """Test all the lovely success cases"""
    for test_json in (PATH_TEST_CASES / 'good_releases').glob('*.json'):
        with test_json.open() as fh_test:
            component_finder.validate_release_schema(json.load(fh_test))

def test_schema_failure():
    """Test all the lovely failure cases"""
    for test_json in (PATH_TEST_CASES / 'bad_releases').glob('*.json'):
        with test_json.open() as fh_test:
            with pytest.raises(jsonschema.ValidationError):
                component_finder.validate_release_schema(json.load(fh_test))

def test_find_current_release():
    """Test our current Release finder"""
    assert component_finder.find_current_release(PATH_TEST_CASES / 'semver_test') == \
        component_finder.Release(PATH_TEST_CASES / 'semver_test' / 'v2.1.0')
