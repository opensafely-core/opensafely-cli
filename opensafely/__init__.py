import argparse
import sys

from opensafely._vendor.jobrunner import local_run
from opensafely import update_codelists


def main():
    parser = argparse.ArgumentParser()

    def show_help(**kwargs):
        parser.print_help()
        parser.exit()

    parser.set_defaults(function=show_help)

    subparsers = parser.add_subparsers(
        title="available commands", description="", metavar="COMMAND"
    )

    parser_help = subparsers.add_parser("help", help="Show this help message and exit")
    parser_help.set_defaults(function=show_help)

    # Add `run` command
    parser_run = subparsers.add_parser("run", help=local_run.DESCRIPTION)
    local_run.add_arguments(parser_run)
    parser_run.set_defaults(function=local_run.main)

    # Add `update_codelists` command
    parser_update_codelists = subparsers.add_parser(
        "update_codelists", help=update_codelists.DESCRIPTION
    )
    update_codelists.add_arguments(parser_update_codelists)
    parser_update_codelists.set_defaults(function=update_codelists.main)

    args = parser.parse_args()
    kwargs = vars(args)
    function = kwargs.pop("function")
    success = function(**kwargs)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
