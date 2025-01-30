import argparse
import logging
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# ensure pkg_resources can find the package metadata we have included, as the
# opentelemetry packages need it
import pkg_resources


opensafely_module_dir = Path(__file__).parent
pkg_resources.working_set.add_entry(f"{opensafely_module_dir}/_vendor")

from opensafely import (  # noqa: E402
    check,
    clean,
    codelists,
    execute,
    extract_stats,
    info,
    jupyter,
    launch,
    pull,
    rstudio,
    unzip,
    upgrade,
)
from opensafely._vendor.jobrunner.cli import local_run  # noqa: E402


# quieten unneeded loggers
logging.getLogger("opensafely._vendor.jobrunner.tracing").setLevel(logging.ERROR)


__version__ = Path(__file__).parent.joinpath("VERSION").read_text().strip()


VERSION_FILE = Path(tempfile.gettempdir()) / "opensafely-version-check"


def should_version_check():
    if not VERSION_FILE.exists():
        return True

    four_hours_ago = datetime.utcnow() - timedelta(hours=4)

    return VERSION_FILE.stat().st_mtime < four_hours_ago.timestamp()


# separated out to be able to used in test setup
def update_version_check():
    VERSION_FILE.touch()


def warn_if_updates_needed(argv):
    # we only check for new versions periodically
    if not should_version_check():
        return

    # we version check before parse_args is called so that if a user is
    # following recent documentation but has an old opensafely installed,
    # there's some hint as to why their invocation is failing before being told
    # by argparse
    if len(argv) == 1 or argv[1] != "upgrade":
        try:
            latest = upgrade.check_version()
            if latest:
                upgrade_command = (
                    "uv tool upgrade opensafely"
                    if upgrade.is_installed_with_uv()
                    else "opensafely upgrade"
                )
                print(
                    f"Warning: there is a newer version of opensafely available ({latest})"
                    f" - please upgrade by running:\n"
                    f"    {upgrade_command}\n",
                    file=sys.stderr,
                )
                # if we're out of date, don't warn the user about out of date images as well
                return
        except Exception:
            pass

    # check for out of date images unless we are updating images.
    if len(argv) == 1 or argv[1] != "pull":
        try:
            need_update = pull.check_version()
            if need_update:
                print(
                    f"Warning: the OpenSAFELY docker images for {', '.join(need_update)} actions are out of date"
                    " - please update by running:\n"
                    "    opensafely pull\n",
                    file=sys.stderr,
                )

        except Exception:
            pass

    update_version_check()


def main():
    parser = argparse.ArgumentParser()

    def show_help(**kwargs):
        parser.print_help()
        parser.exit()

    parser.set_defaults(function=show_help)
    parser.add_argument(
        "--version", action="version", version=f"opensafely {__version__}"
    )
    parser.add_argument(
        "--debug",
        "-d",
        dest="global_debug",
        action="store_true",
        help="display debugging information",
    )

    subparsers = parser.add_subparsers(
        title="available commands", description="", metavar="COMMAND"
    )

    parser_help = subparsers.add_parser("help", help="Show this help message and exit")
    parser_help.set_defaults(function=show_help)

    def add_subcommand(cmd, module):
        subparser = subparsers.add_parser(cmd, help=module.DESCRIPTION)
        subparser.set_defaults(function=module.main)
        module.add_arguments(subparser)

    add_subcommand("run", local_run)
    add_subcommand("codelists", codelists)
    add_subcommand("pull", pull)
    add_subcommand("upgrade", upgrade)
    add_subcommand("check", check)
    add_subcommand("unzip", unzip)
    add_subcommand("extract-stats", extract_stats)
    add_subcommand("info", info)
    add_subcommand("exec", execute)
    add_subcommand("clean", clean)
    add_subcommand("launch", launch)

    # deprecated
    add_subcommand("jupyter", jupyter)
    add_subcommand("rstudio", rstudio)

    warn_if_updates_needed(sys.argv)
    args = parser.parse_args()
    kwargs = vars(args)

    function = kwargs.pop("function")
    debug = kwargs.pop("global_debug")

    if debug:
        os.environ["DEBUG"] = "true"

    try:
        success = function(**kwargs)
    except Exception as exc:
        if debug:
            raise
        else:
            print(str(exc), file=sys.stderr)
        success = False

    # if `run`ning locally, run `check` in warn mode
    if function == local_run.main and "format-output-for-github" not in kwargs:
        check.main(continue_on_error=True)

    # allow functions to return True/False, or an explicit exit code
    if success is False:
        exit_code = 1
    elif success is True:
        exit_code = 0
    else:
        exit_code = success

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
