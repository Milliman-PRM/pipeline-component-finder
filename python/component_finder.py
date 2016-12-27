"""
### CODE OWNERS: Shea Parkes, Kyle Baird

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
import datetime
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
        return self.path.parent.name.lower()

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

    def generate_setup_env_code(self, analytics_pipeline: bool=False) -> 'typing.List[str]':
        """Generate the code to setup environment variables for this component"""
        _code = []
        _code.append('rem Component: {}    Version: {}'.format(
            self.component_name,
            self.version,
        ))
        _code.append('rem Primary Signer: {}    Peer Reviewer: {}'.format(
            self.release_json['qrm']['primary_signer'],
            self.release_json['qrm']['peer_reviewer'],
        ))
        _code.append('rem QRM Documentation: {}'.format(
            self.release_json['qrm']['documentation_home'],
        ))
        if analytics_pipeline:
            _code.append('SET PRM_COMPONENTS={}'.format(self.component_name.upper()))
        else:
            _code.append(
                'SET PRM_COMPONENTS=%PRM_COMPONENTS%;{}'.format(self.component_name.upper())
            )
        _code.append('SET {}_HOME={}{}'.format(
            self.component_name.upper(),
            self.path,
            os.path.sep,
        ))
        _code.append('rem SET {}_HOME=%UserProfile%\\repos\\{}{}'.format(
            self.component_name.upper(),
            self.name_git_repo,
            os.path.sep,
        ))
        _code.append('SET {}_URL_GIT={}'.format(
            self.component_name.upper(),
            self.url_git_repo,
        ))
        if not analytics_pipeline: # `analytics_pipeline_env.bat` seeds %PYTHONPATH%
            _code.append('SET PYTHONPATH=%PYTHONPATH%;%{}_HOME%python'.format(
                self.component_name.upper(),
            ))
        if self.path_qvws_git:
            _code.append('SET {}_GIT_QVW_PATH={}{}'.format(
                self.component_name.upper(),
                self.path_qvws_git,
                os.path.sep,
            ))
        return _code


def find_current_release(path: Path) -> typing.Optional[Release]:
    """Find the current release from a folder of releases"""
    releases = []
    with contextlib.suppress(OSError):
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

    name_output = 'pipeline_components_env-{}.bat'.format(
        datetime.datetime.now().strftime('%Y-%m-%d'),
    )
    LOGGER.info('Writing setup code into %s', name_output)
    with open(name_output, 'w') as fh_out:
        fh_out.write('rem Auto-generated on {} by {}\n\n'.format(
            datetime.datetime.now(),
            os.environ['UserName'],
        ))
        fh_out.write('rem Objective: Setup comprehensive environment for PRM pipeline work\n\n')
        fh_out.write('rem Developer Notes:\n')
        fh_out.write('rem   Intended to ultimately reside in a deliverable folder (i.e. next to `open_prm.bat`)\n\n\n')

        anal_pipe = components.pop('analytics_pipeline')
        LOGGER.info('Beginning special treatment of %s', anal_pipe)
        for line in anal_pipe.generate_setup_env_code(analytics_pipeline=True):
            fh_out.write('' + line + '\n')
        fh_out.write('\nrem Calling embedded `prm_env.bat`\n')
        fh_out.write('rem   This will seed some accumulators (e.g. PYTHONPATH)\n')
        fh_out.write('call %ANALYTICS_PIPELINE_HOME%prm_env.bat\n\n\n')
        LOGGER.info('Finished special treatment of %s', anal_pipe)

        for component in components.values():
            LOGGER.info('Generating setup code for %s', component)
            for line in component.generate_setup_env_code():
                fh_out.write(line + '\n')
            fh_out.write('\n\n')

        LOGGER.info('Adding an entry for a client specific library')
        fh_out.write('rem Include any client-specific python libraries\n')
        fh_out.write('SET PYTHONPATH=%PYTHONPATH%;%~dp0\\01_Programs\\python\n')

    LOGGER.info('Finished generating %s', name_output)
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
