import subprocess
import sys


DESCRIPTION = (
    "Command to clean up old OpenSAFELY docker containers, volumes and images."
)

# images and jobs can be selected with this
label_filter = "label=org.opencontainers.image.vendor=OpenSAFELY"
# busy box doesn't have the vendor, so use the image name
busybox_filter = "ancestor=ghcr.io/opensafely-core/busybox"
# catch all prefix for any old jobs lying around
name_filter = "name=os-job-"
# volumes don't currently have labels, so use name prefix
volume_filter = "name=os-volume-"


def add_arguments(parser):
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print all commands and error messages for debugging",
    )


def docker_output(cmd, verbose=False):
    full = ["docker"] + cmd
    if verbose:
        print(" ".join(full))
    try:
        ps = subprocess.run(full, check=True, capture_output=True, text=True)
        output = ps.stdout.strip()
        if output:
            return output.splitlines()
        else:
            return []
    except subprocess.CalledProcessError as exc:
        if verbose:
            print(exc.stderr, file=sys.stderr)


def clean_images(verbose=False):
    print("Pruning old OpenSAFELY docker images...")
    docker_output(["image", "prune", "--force", "--filter", label_filter], verbose)


def main(verbose=False):
    filters = [label_filter, busybox_filter, name_filter, volume_filter]
    containers = set()
    for f in filters:
        containers |= set(
            docker_output(
                ["container", "ls", "--all", "--format={{ .ID }}", "--filter", f],
                verbose,
            )
        )

    if containers:
        print(f"Removing {len(containers)} OpenSAFELY containers...")
        docker_output(["rm", "--force"] + list(sorted(containers)), verbose)

    # find and remove any volumes (not labelled currently)
    volumes = docker_output(
        ["volume", "ls", "--format={{ .Name }}", "--filter", volume_filter], verbose
    )
    if volumes:
        print(f"Removing {len(volumes)} OpenSAFELY volumes...")
        docker_output(["volume", "rm", "--force"] + volumes, verbose)

    clean_images(verbose)
