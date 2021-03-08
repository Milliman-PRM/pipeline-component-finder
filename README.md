# PRM Pipeline Component Finder

A repository for tooling that helps bring the various PRM pipeline components together.

Specifically, it aids in finding the current version of all pipeline components and compiling that information into a fresh copy of `pipeline_components_env.bat`

### Development Guidelines

This repository will follow [GitHub Flow](https://guides.github.com/introduction/flow/index.html) as shown here:

![Github-Flow](github-flow.jpg "GitHub Flow")

There are no formal releases of this solution itself; the `master` branch is always live.

## Usage / Result Promotion

This pipeline component finder can be executed by building a specific job on Jenkins, and it should be executed anytime a new release of any pipeline component has been made available.  Simply go to the [PRM_Pipeline_ENV_Generator job](https://indy-jenkins.milliman.com/job/PRM_Pipeline_ENV_Generator/) on `indy-jenkins` and trigger a build with the default parameters.  This will create and deploy a new `pipeline_components_env.bat` file to the network.  Anyone with access to `indy-jenkins` should be able to trigger a build of this job.

### Underlying details of usage

Although [the Jenkins job](https://indy-jenkins.milliman.com/job/PRM_Pipeline_ENV_Generator/) above should be used for most production scenarios, it can still be important to understand how to execution this solution without Jenkins (e.g. when troubleshooting errors, when developing changes to this solution, or when updating that Jenkins job itself).

This pipeline component finder will validate each release of each pipeline component.  In particular, it will confirm:
  - The pipeline component was promoted into an appropriate folder under `S:\PRM\Pipeline_Components\`
  - A valid semantic version was utilized
  - A `release.json` was included in each release.  It must contain specific documentation of release peer review and the contents will be validated against the embedded `python\release-schema.json` file from this repository.

If there are any documentation or folder structure issues, the pipeline component finder will fail with a hopefully helpful message.

The `component_finder` module of this solution is setup to be executable, so users can run the solution from the command line with `python -m component_finder`.

After successful execution, the new `pipeline_components_env.bat` should be promoted to `S:\PRM\Pipeline_Components_Env\`.  New production runs will cache the latest version of `pipeline_components_env.bat` from there (so existing production runs will not be disrupted).

Here is a complete example of running the pipeline component finder and promoting its output:

```bat
setup_env.bat
python -m component_finder
copy pipeline_components_env-YYYY-MM-DD.bat s:\PRM\Pipeline_Components_Env\pipeline_components_env-YYYY-MM-DD.bat
copy pipeline_components_env-YYYY-MM-DD.bat s:\PRM\Pipeline_Components_Env\pipeline_components_env.bat
```
