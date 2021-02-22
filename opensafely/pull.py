import subprocess
import sys

from opensafely._vendor.jobrunner import config


DESCRIPTION = (
    "Command for updating the docker images used to run OpenSAFELY studies locally"
)
REGISTRY = config.DOCKER_REGISTRY
IMAGES = list(config.ALLOWED_IMAGES)
DEPRECATED_REGISTRIES = ["docker.opensafely.org", "ghcr.io/opensafely"]
IMAGES.sort()  # this is just for consistency for testing


def add_arguments(parser):
    choices = ["all"] + IMAGES
    parser.add_argument(
        "image",
        nargs="?",
        choices=choices,
        help="OpenSAFELY docker image to update (default: all)",
        default="all",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Update docker images even if not present locally",
    )


def main(image, force):
    if image == "all":
        images = IMAGES
    else:
        # if user has requested a specific image, pull it regardless
        force = True
        images = [image]

    local_images = get_local_images()
    try:
        updated = False
        for image in images:
            tag = f"{REGISTRY}/{image}"
            if force or tag in local_images:
                updated = True
                print(f"Updating OpenSAFELY {image} image")
                subprocess.run(["docker", "pull", tag + ":latest"], check=True)

        if updated:
            print("Cleaning up old images")
            remove_deprecated_images(local_images)
            subprocess.run(["docker", "image", "prune", "--force"], check=True)
        else:
            print("No OpenSAFELY docker images found to update.")

    except subprocess.CalledProcessError as exc:
        sys.exit(exc.stderr)


def get_local_images():
    ps = subprocess.run(
        ["docker", "image", "ls", "--format={{.Repository}}"],
        check=True,
        text=True,
        capture_output=True,
    )
    lines = [line for line in ps.stdout.splitlines() if line.strip()]
    return set(lines)


def remove_deprecated_images(local_images):
    """Temporary clean up functon to remove orphaned images."""
    for registry in DEPRECATED_REGISTRIES:
        for image in IMAGES:
            tag = f"{registry}/{image}"
            if tag in local_images:
                subprocess.run(["docker", "image", "rm", tag], capture_output=True)
