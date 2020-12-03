# OpenSAFELY Command Line Interface

This tool is part of the [OpenSAFELY](https://www.opensafely.org)
project.

To use it you will need to install:
 * [Python](https://www.python.org/downloads/) (at least version 3.7, but the more recent the better)
 * [git](https://git-scm.com/downloads)
 * [Docker](https://docs.docker.com/get-docker/)

Once these are installed you can install the tool itself with:
```
pip install opensafely
```

To see available commands run
```
opensafely --help
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
