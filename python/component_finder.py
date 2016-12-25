"""
### CODE OWNERS: Shea Parkes

### OBJECTIVE:
  Library code to aid in finding product components.

### DEVELOPER NOTES:
  <None>
"""
import logging
import json
import typing
from pathlib import Path

import jsonschema

LOGGER = logging.getLogger(__name__)
with (Path(__file__).parent / 'release-schema.json').open() as fh_schema:
    SCHEMA_RELEASE = json.load(fh_schema)

# =============================================================================
# LIBRARIES, LOCATIONS, LITERALS, ETC. GO ABOVE HERE
# =============================================================================

def validate_release_schema(release) -> None:
    """Validate a candidate release against the anticipated schema."""
    jsonschema.validate(release, SCHEMA_RELEASE)
    if release['qrm']['primary_signer'] == release['qrm']['peer_reviewer']:
        raise jsonschema.ValidationError(
            'Primary Signer and Peer Reviewer cannot both be {}'.format(
                release['qrm']['primary_signer'],
            )
        )

    return None

def find_current_semver(path: Path) -> typing.Optional[Path]:
    """Find the current release from a folder of releases"""
    return path
