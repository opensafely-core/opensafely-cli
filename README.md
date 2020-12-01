# OpenSAFELY Command Line Interface

_User-facing documentation to go here_


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
