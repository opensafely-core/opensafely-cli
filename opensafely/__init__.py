import argparse
import sys
from pathlib import Path

from opensafely import check, codelists, jupyter, pull, upgrade
from opensafely._vendor.jobrunner.cli import local_run

__version__ = Path(__file__).parent.joinpath("VERSION").read_text().strip()


def main():
    parser = argparse.ArgumentParser()
    supports_unknown_args = set()

    def show_help(**kwargs):
        parser.print_help()
        parser.exit()

    parser.set_defaults(function=show_help)
    parser.add_argument(
        "--version", action="version", version=f"opensafely {__version__}"
    )

    subparsers = parser.add_subparsers(
        title="available commands", description="", metavar="COMMAND"
    )

    parser_help = subparsers.add_parser("help", help="Show this help message and exit")
    parser_help.set_defaults(function=show_help)

    def add_subcommand(cmd, module):
        subparser = subparsers.add_parser(cmd, help=local_run.DESCRIPTION)
        subparser.set_defaults(function=module.main)
        handles_unknown = module.add_arguments(subparser)
        if handles_unknown:
            supports_unknown_args.add(module.main)

    add_subcommand("run", local_run)
    add_subcommand("codelists", codelists)
    add_subcommand("pull", pull)
    add_subcommand("upgrade", upgrade)
    add_subcommand("check", check)
    add_subcommand("jupyter", jupyter)

    # we version check before parse_args is called so that if a user is
    # following recent documentation but has an old opensafely installed,
    # there's some hint as to why their invocation is failing before being told
    # by argparse.
    if len(sys.argv) == 1 or sys.argv[1] != "upgrade":
        upgrade.check_version()

    # start by using looser parsing only known args, so we can get the sub command
    args, unknown = parser.parse_known_args()

    #
    if args.function in supports_unknown_args:
        kwargs = vars(args)
        kwargs["unknown_args"] = unknown
    # allow supparsers to opt out of looser parser_known_args parsing
    else:
        # reparse args with stricter semantics
        args = parser.parse_args()
        kwargs = vars(args)

    function = kwargs.pop("function")
    success = function(**kwargs)

    # if `run`ning locally, run `check` in warn mode
    if function == local_run.main and "format-output-for-github" not in kwargs:
        check.main(continue_on_error=True)

    sys.exit(0 if success is not False else 1)


if __name__ == "__main__":
    main()
