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
import functools
import contextlib
from pathlib import Path

import jsonschema
from semantic_version import Version

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


@functools.total_ordering
class Release():
    """Class to encapsulate the fun of a release"""

    def __init__(self, path: Path) -> None:
        """Setup the fun"""
        if not path.is_dir():
            raise ValueError('{} is not a directory')
        self.path = path
        self.version = Version(self.path.name[1:]) # Strip off leading 'v'

    def validate_release_json(self) -> None:
        """Validate the embedded release.json"""
        validate_release_schema(self.path / 'release.json')

    def __getattr__(self, name):
        """Pass through to embedded Version class"""
        return getattr(self.version, name)

    def __eq__(self, other):
        """Compare on version"""
        return self.version == other.version

    def __lt__(self, other):
        """Sort on version"""
        return self.version < other.version

    def __repr__(self):
        """A pretty stringifyier"""
        return "Release(path={}, version={})".format(
            self.path,
            self.version,
        )


def find_current_release(path: Path) -> typing.Optional[Release]:
    """Find the current release from a folder of releases"""
    releases = []
    for possible_release in path.glob('*'):
        with contextlib.suppress(ValueError):
            version = Release(possible_release)
            if not version.prerelease:
                releases.append(version)

    if releases:
        releases.sort()
        return releases[-1]
    else:
        return None
