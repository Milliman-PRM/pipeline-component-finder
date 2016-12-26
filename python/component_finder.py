"""
### CODE OWNERS: Shea Parkes

### OBJECTIVE:
  Library code to aid in finding product components.

### DEVELOPER NOTES:
  <None>
"""
import os
import logging
import json
import typing
import functools
import contextlib
from pathlib import Path

import jsonschema
from semantic_version import Version
from yarl import URL

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

    _url_git_repo = URL(release['url_git_repo'])
    _repo_name = _url_git_repo.name
    if not _repo_name:
        raise jsonschema.ValidationError(
            '{} is likely ending with a front slash and should not'.format(_url_git_repo)
        )
    if 'git' in _repo_name.lower():
        raise jsonschema.ValidationError(
            '"git" should not be in {}'.format(_repo_name)
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
        self._release_json = None # Lazily loaded for backward compatibility

    @property
    def release_json(self):
        """Lazily load (and validate) the accompanying release.json"""
        if self._release_json:
            return self._release_json
        else:
            path_release_json = self.path / 'release.json'
            assert path_release_json.is_file(), '{} does not exist'.format(path_release_json)
            with path_release_json.open() as fh_json:
                self._release_json = json.load(fh_json)
            validate_release_schema(self._release_json)
            return self._release_json

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
        return "Release(component_name={}, version={}, path={})".format(
            self.component_name,
            self.version,
            self.path,
        )

    @property
    def component_name(self):
        """Dig out the component name from the path."""
        return self.path.parent.name.upper()

    @property
    def url_git_repo(self) -> URL:
        """Where the code for the component likely lives"""
        return URL(self.release_json['url_git_repo'])

    @property
    def name_git_repo(self) -> str:
        """Get the name of the git repo for this component"""
        return self.url_git_repo.name.lower()

    @property
    def path_qvws_git(self) -> typing.Optional[Path]:
        """Lazily provide the path to compiled QVWs for use with checked out code"""
        try:
            _path_qvws_git = Path(self.release_json['path_qvws_git'])
            # Lazily validated to keep file system coupling minimal
            assert _path_qvws_git.is_dir(), '{} does not exist'.format(_path_qvws_git)
            return _path_qvws_git
        except KeyError:
            return None

    def generate_setup_env_code(self):
        """Generate the code to setup environment variables for this component"""
        _code = []
        _code.append(
            'SET PRM_COMPONENTS=%PRM_COMPONENTS%;{}'.format(self.component_name)
        )
        _code.append('SET {}_HOME={}{}'.format(
            self.component_name,
            self.path,
            os.path.sep,
        ))
        _code.append('rem SET {}_HOME=%UserProfile%\\repos\\{}{}'.format(
            self.component_name,
            self.name_git_repo,
            os.path.sep,
        ))
        _code.append('SET {}_URL_GIT={}'.format(
            self.component_name,
            self.url_git_repo,
        ))
        _code.append('SET PYTHONPATH=%PYTHONPATH%;{}'.format(
            self.path / 'python',
        ))
        if self.path_qvws_git:
            _code.append('SET {}_GIT_QVW_PATH={}{}'.format(
                self.component_name,
                self.path_qvws_git,
                os.path.sep,
            ))
        return _code


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


def main(root_path: Path) -> int:
    """Do the real work"""
    LOGGER.info('Going to assemble a new `prm_env_components.bat`')

    LOGGER.info('Scanning for product components here: %s', root_path)
    components = {}
    for subdir in root_path.glob('*'):
        if not subdir.is_dir():
            continue
        release = find_current_release(subdir)
        if not release:
            continue
        LOGGER.info('Found %s', release)
        components[subdir.name.lower()] = release

    return 0


if __name__ == '__main__':
    # pylint: disable=wrong-import-position, wrong-import-order
    import sys
    logging.basicConfig(
        format='%(asctime)s|%(name)s|%(levelname)s|%(message)s',
        level=logging.INFO,
    )
    RETURN_CODE = main(Path('S:/PRM'))
    sys.exit(RETURN_CODE)
