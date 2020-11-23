import argparse
import sys

from jobrunner import local_run


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

    parser_run = subparsers.add_parser("run", help=local_run.HELP)
    local_run.add_arguments(parser_run)
    parser_run.set_defaults(function=local_run.main)

    args = parser.parse_args()
    kwargs = vars(args)
    function = kwargs.pop("function")
    success = function(**kwargs)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
