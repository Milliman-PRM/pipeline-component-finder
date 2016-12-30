# PRM Pipeline Component Finder

A repository for tooling that helps bring the various PRM pipeline components together.

Specifically, it aids in finding the current version of all pipeline components and compiling that information into a fresh copy of `pipeline_components_env.bat`

### Development Guidelines

This repository will follow [GitHub Flow](https://guides.github.com/introduction/flow/index.html) as shown here:

![Github-Flow](github-flow.jpg "GitHub Flow")

## Usage / Result Promotion

For now, the intention is to manually run the component finder and copy the results to the network.  Current promotion home is `S:\PRM\Pipeline_Components_Env\`

For example:

```bat
setup_env.bat
python -m component_finder
copy pipeline_components_env-YYYY-MM-DD.bat s:\PRM\Pipeline_Components_Env\pipeline_components_env-YYYY-MM-DD.bat
copy pipeline_components_env-YYYY-MM-DD.bat s:\PRM\Pipeline_Components_Env\pipeline_components_env.bat
```
