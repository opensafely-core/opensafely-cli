from pathlib import Path
import subprocess
import sys

from opensafely._vendor.jobrunner import config
from opensafely._vendor.jobrunner.local_run import docker_preflight_check
from opensafely._vendor.ruamel.yaml import YAML
from opensafely._vendor.ruamel.yaml.error import YAMLError, YAMLStreamError, YAMLWarning, YAMLFutureWarning


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
    parser.add_argument(
        "--project",
        help="Use this project to yaml to decide which images to download",
    )


def main(image="all", force=False, project=None):
    if not docker_preflight_check():
        return False

    if project:
        force = True
        images = get_actions_from_project_file(project)
    elif image == "all":
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


def get_actions_from_project_file(project_yaml):
    path = Path(project_yaml)
    if not path.exists():
        raise RuntimeError(f"Could not find {project_yaml}")

    try:
        with path.open() as f:
            project = YAML(typ="safe", pure=True).load(path)
    except (YAMLError, YAMLStreamError, YAMLWarning, YAMLFutureWarning) as e:
        raise RuntimeError(f"Could not parse {project_yaml}: str(e)")

    images = []
    for action_name, action in project.get("actions", {}).items():
        if not action:
            continue
        command = action.get("run", None)
        if command is None:
            continue

        name, _, version = command.partition(":")
        if name in IMAGES:
            images.append(name)

    if not images:
        raise RuntimeError(f"No actions found in {project_yaml}")

    return images


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
