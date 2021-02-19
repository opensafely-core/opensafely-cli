import subprocess
import sys


DESCRIPTION = (
    "Command for updating the docker images used to run OpenSAFELY studies locally"
)
REGISTRY = "ghcr.io/opensafely-core"
IMAGES = ["r", "python", "jupyter", "stata-mp"]


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

    try:
        updated = False
        for image in images:
            tag = f"{REGISTRY}/{image}:latest"
            if force or tag_present(tag):
                updated = True
                print(f"Updating OpenSAFELY {image} image")
                subprocess.run(["docker", "pull", tag], check=True)

        if updated:
            print("Cleaning up old images")
            subprocess.run(["docker", "image", "prune", "--force"], check=True)
        else:
            print("No OpenSAFELY docker images found to update.")

    except subprocess.CalledProcessError as exc:
        sys.exit(exc.output)


def tag_present(tag):
    ps = subprocess.run(["docker", "image", "inspect", tag], capture_output=True)
    return ps.returncode == 0
