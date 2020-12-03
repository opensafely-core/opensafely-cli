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

The tool makes the process fairly painless. There are a few things
workaround we needed to apply which are all configured in
[pyproject.toml](./pyproject.toml).

To update the versions of vendored dependencies:

1. Install the developer tooling:
   ```
   pip install -r requirements.dev.txt
   ```

2. Compile the vendor requirements file:
   ```
   pip-compile vendor.in
   ```

3. Awkward bit: edit `vendor.txt` to comment out the ruamel C library:
   ```
   # ruamel.yaml.clib==0.2.2   # via ruamel.yaml
   ```
   This is a binary dependency which we obviously can't vendor, but I
   can't find a way to exclude this automatically.

4. Run the vendoring tool:
   ```
   vendoring sync -v
   ```

5. Commit the updated files in `opensafely/_vendor`
