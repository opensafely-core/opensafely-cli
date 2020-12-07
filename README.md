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

**Note on Python versions:** We currently need to support Python 3.7 and
up as, historically, some researchers had 3.7 easily available but not
3.8. Further down the line we'll probably aim to ship our own
self-contained executable so we'll be able to use whatever Python
version we want.

However, the [vendoring](https://pypi.org/project/vendoring/) tool (see
below) needs 3.8+ so we have to use 3.8 for developing with. The tests
run under 3.7 in CI which should guard against accidental 3.8isms
creeping in.


### Vendoring

To minimise the possibility for installation issues this package vendors
all its dependencies under the [opensafely._vendor](./opensafely/_vendor)
namespace using the [vendoring](https://pypi.org/project/vendoring/) tool.

This brings its own complexities (particularly around the `requests`
package) but they are at least complexities which show up at development
time rather than on some researcher's mysteriously broken Python
installation.

The tool makes the process relatively painless. There are a few
workarounds (crude string subsitutions) we need to apply which are all
configured in [pyproject.toml](./pyproject.toml).

To update the versions of vendored dependencies:

1. Install the developer tooling (you'll need Python 3.8 for this):
   ```
   pip install -r requirements.dev.txt
   ```

2. Run the update script:
   ```
   ./scripts/update-dependencies.sh
   ```


### Tests

Test with:
```
python -m pytest
```

Due to the fact that we're vendoring `requests` there's some slightly
nasty monkeypatching which we need to apply `requests_mock` in order to
get it to mock the right library. Monkeypatching mocking libraries is
known as "software engineering".
