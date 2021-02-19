import argparse
from pathlib import Path
import sys

from opensafely._vendor.jobrunner import local_run
from opensafely import codelists, pull


__version__ = Path(__file__).parent.joinpath("VERSION").read_text().strip()


def main():
    parser = argparse.ArgumentParser()

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

    # Add `run` subcommand
    parser_run = subparsers.add_parser("run", help=local_run.DESCRIPTION)
    parser_run.set_defaults(function=local_run.main)
    local_run.add_arguments(parser_run)

    # Add `codelists` subcommand
    parser_codelists = subparsers.add_parser("codelists", help=codelists.DESCRIPTION)
    parser_codelists.set_defaults(function=codelists.main)
    codelists.add_arguments(parser_codelists)

    # Add `pull` subcommand
    parser_pull = subparsers.add_parser("pull", help=pull.DESCRIPTION)
    parser_pull.set_defaults(function=pull.main)
    pull.add_arguments(parser_pull)

    args = parser.parse_args()
    kwargs = vars(args)
    function = kwargs.pop("function")
    success = function(**kwargs)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
