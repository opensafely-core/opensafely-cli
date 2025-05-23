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

## Updating Job Runner

Historically, this repo consumed [`job-runner`](https://github.com/opensafely-core/job-runner)
as a Python package (vendored like all other dependencies) which was used to provide the
`opensafely run` command.

However this has now changed. See the notes in this issue for more details:
https://github.com/opensafely-core/opensafely-cli/issues/330

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
according to information parsed from the commits using semantic-release conventions (e.g. `fix:`, `feat:`).
If no semantic commit is found since the last tag, a new version
will not be released.

## Local Builds

Making a local build can be useful for testing and QA purposes.
This is done by running:
```
python setup.py sdist bdist_wheel
```

which will output a `.tar.gz` and `.whl` file in the `dist/` directory.
The latter of which can be passed to `pip install` for installation,
ideally in a separate virtual environment for testing/QA purposes.
