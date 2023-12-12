import argparse
import subprocess
import sys
from http.cookiejar import split_header_words
from pathlib import Path
from urllib.parse import urlparse

from opensafely._vendor import pipeline, requests
from opensafely._vendor.jobrunner import config
from opensafely._vendor.jobrunner.cli.local_run import docker_preflight_check
from opensafely.clean import clean_images


DESCRIPTION = (
    "Command for updating the docker images used to run OpenSAFELY studies locally"
)
REGISTRY = config.DOCKER_REGISTRY
# The deprecated `databuilder` name is still supported by job-runner, but we don't want
# it showing up here
IMAGES = list(config.ALLOWED_IMAGES - {"databuilder"})
DEPRECATED_REGISTRIES = ["docker.opensafely.org", "ghcr.io/opensafely"]
IMAGES.sort()  # this is just for consistency for testing


def valid_image(image_string):
    if image_string == "all":
        return image_string

    name, _, _ = image_string.partition(":")
    if name not in IMAGES:
        raise argparse.ArgumentTypeError(
            f"{image_string} is not a valid OpenSAFELY image: {','.join(IMAGES)}"
        )

    return image_string


def add_arguments(parser):
    parser.add_argument(
        "image",
        nargs="?",
        help="OpenSAFELY docker image to update (default: all)",
        type=valid_image,
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

    local_images = get_local_images()

    if project:
        force = True
        images = get_actions_from_project_file(project)
    elif image == "all":
        if force:
            images = {
                f"{name}:{get_default_version_for_image(name)}": None for name in IMAGES
            }
        else:
            images = list(local_images)
    else:
        # if user has requested a specific image, pull it regardless
        force = True
        images = [image]

    try:
        updated = False
        for image in images:
            if force or image in local_images:
                name, _, tag = image.partition(":")
                if not tag:
                    tag = get_default_version_for_image(name)
                updated = True

                print(f"Updating OpenSAFELY {name}:{tag} image")
                subprocess.run(
                    ["docker", "pull", f"{REGISTRY}/{name}:{tag}"], check=True
                )

        if updated:
            remove_deprecated_images(local_images)
            clean_images()
        else:
            print("No OpenSAFELY docker images found to update.")

    except subprocess.CalledProcessError as exc:
        sys.exit(exc.stderr)


def get_actions_from_project_file(project_yaml):
    try:
        project = pipeline.load_pipeline(Path(project_yaml))
    except pipeline.ProjectValidationError as exc:
        raise RuntimeError(f"Invalid project.yaml {project_yaml}: {exc}")

    images = []

    for name, action in project.actions.items():
        if action.run.name in IMAGES and action.run.name not in images:
            images.append(f"{action.run.name}:{action.run.version}")

    if not images:
        raise RuntimeError(f"No actions found in {project_yaml}")

    return images


def get_local_images():
    """Returns a dict of image names and their locally available SHAs"""
    ps = subprocess.run(
        [
            "docker",
            "images",
            "ghcr.io/opensafely-core/*",  # this excludes dev builds
            "--filter",
            "label=org.opensafely.action",
            "--no-trunc",
            "--format={{.Repository}}:{{.Tag}}={{.ID}}",
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    images = dict()
    for line in ps.stdout.splitlines():
        if not line.strip():
            continue

        line = line.replace("ghcr.io/opensafely-core/", "")

        image, sha = line.split("=", 1)
        images[image] = sha

    return images


def remove_deprecated_images(local_images):
    """Temporary clean up functon to remove orphaned images."""
    for registry in DEPRECATED_REGISTRIES:
        for image in IMAGES:
            tag = f"{registry}/{image}"
            if tag in local_images:
                subprocess.run(["docker", "image", "rm", tag], capture_output=True)


def get_default_version_for_image(name):
    if name in ["ehrql"]:
        return "v1"
    elif name == "python":
        return "v2"
    else:
        return "latest"


session = requests.Session()
token = None


def dockerhub_api(path):
    """Get the current sha for a tag from a docker registry."""
    global token

    url = f"https://ghcr.io/{path}"

    # Docker API requires auth token, even for public resources.
    # However, we can reuse a public token.
    if token is None:
        response = session.get(url)
        token = get_auth_token(response.headers["www-authenticate"])
    else:
        response = session.get(url, headers={"Authorization": f"Bearer {token}"})

    # refresh token if needed
    if response.status_code == 401:
        token = get_auth_token(response.headers["www-authenticate"])
        response = session.get(url, headers={"Authorization": f"Bearer {token}"})

    response.raise_for_status()
    return response.json()


def get_remote_sha(full_name, tag):
    """Get the current sha for a tag from a docker registry."""
    parsed = urlparse("https://" + full_name)
    response = dockerhub_api(f"/v2/{parsed.path}/manifests/{tag}")
    return response["config"]["digest"]


def get_auth_token(header):
    """Parse a docker v2 www-authentication header and fetch a token.

    Bearer realm="https://ghcr.io/token",service="ghcr.io",scope="repository:opensafely-core/busybox:pull"
    """
    header = header.lstrip("Bearer")
    # split_header_words is weird, but better than doing it ourselves
    words = split_header_words([header])
    values = dict(next(zip(*words)))
    url = values.pop("realm")
    auth_response = session.get(url, params=values)
    return auth_response.json()["token"]


def check_version():
    need_update = []
    local_images = get_local_images()

    for image, local_sha in local_images.items():
        name, _, tag = image.partition(":")
        latest_sha = get_remote_sha(f"{REGISTRY}/{name}", tag)
        if latest_sha != local_sha:
            need_update.append(image)

    if need_update:
        print(
            f"Warning: the OpenSAFELY docker images for {', '.join(need_update)} actions are out of date - please update by running:\n"
            "    opensafely pull\n",
            file=sys.stderr,
        )
    return need_update
