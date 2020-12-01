# OpenSAFELY Command Line Interface

This tool is part of the [OpenSAFELY](https://www.opensafely.org)
project.

To use it you will need:
 * Python version 3.7 or above
 * git
 * Docker

Once these are installed you can install the tool itself with:
```
pip install opensafely
```

At present there is one command, which can be used to run actions in an
OpenSAFELY project:
```
usage: opensafely run [-h] [-f] [--project-dir PROJECT_DIR] [actions [actions ...]]

positional arguments:
  actions               Name of project action to run

optional arguments:
  -h, --help            show this help message and exit
  -f, --force-run-dependencies
                        Re-run from scratch without using existing outputs
  --project-dir PROJECT_DIR
                        Project directory (default: current directory)
```


## Developer docs

To minimise the possibility for installation issues this package vendors
all its dependencies under the [opensafely._vendor](./opensafely/_vendor)
namespace using the [vendoring](https://pypi.org/project/vendoring/) tool.

Note that while the `opensafely-jobrunner` package technically depends
on `requests` this is only used by the `jobrunner.sync` module which is
never invoked by this interface (as smoketests will confirm).

To update the vendored dependencies first update the versions in
[vendor.txt](./vendor.txt).

Install the developer tooling:
```
pip install -r requirements.dev.txt
```

Run the vendoring tool:
```
vendoring sync -v
```

Finally commit the result.
