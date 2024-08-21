# Developer docs

## Vendoring

To minimise the possibility for installation issues this package vendors
all its dependencies under the [`opensafely._vendor`](./opensafely/_vendor)
namespace using the [vendoring](https://pypi.org/project/vendoring/) tool.

This brings its own complexities (particularly around the `requests`
package) but they are at least complexities which show up at development
time rather than on some researcher's mysteriously broken Python
installation.

The tool makes the process relatively painless. There are a few
workarounds (crude string subsitutions) we need to apply which are all
configured in [pyproject.toml](./pyproject.toml).

To update the vendored version of job-runner:

1. Install the developer tooling (you'll need Python 3.8 for this):
   ```
   pip install -r requirements.dev.txt
   ```

2. Run the update script. It will default to latest tag, but you can pass
   a specific job-runner tag.
   ```
   ./scripts/update.sh [version_tag]
   ```

3. Commit the results


## Tests

Test with:
```
python -m pytest
```

Due to the fact that we're vendoring `requests` there's some slightly
nasty monkeypatching which we need to apply `requests_mock` in order to
get it to mock the right library. Monkeypatching mocking libraries is
known as "software engineering".


## Releases

New versions are tagged, and the PyPI package built and published, automatically
via GitHub actions on merges to `main`.  Note that the version will be bumped
according to information parsed from the commits using semantic-release conventions (e.g. `fix:`, `feat:`).  If no semantic commit is found since the last tag, a new version
will not be released.
