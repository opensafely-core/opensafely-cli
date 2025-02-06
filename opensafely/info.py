import argparse
import json
import subprocess

import opensafely
from opensafely import pull


DESCRIPTION = "Print information about the opensafely tool and available resources"


def add_arguments(parser):
    # developer tool to print the list of versions in project.yaml
    parser.add_argument(
        "--list-project-images",
        nargs="?",  # Makes the value optional
        const="project.yaml",  # Used when flag is present without value
        default=None,  # Used when flag is absent
        help=argparse.SUPPRESS,
    )


INFO = """
opensafely version: {version}
docker version: {docker_version}
docker memory: {memory}
docker cpu: {cpu}
"""


def main(list_project_images=None):

    if list_project_images is not None:
        images = pull.get_actions_from_project_file(list_project_images)
        # part of transitioning away from using :latest in project.yaml
        print("\n".join(i.replace(":latest", ":v1") for i in sorted(images)))
        return True

    print("System information:")
    try:
        ps = subprocess.run(
            ["docker", "info", "-f", "{{json .}}"], capture_output=True, text=True
        )
        info = json.loads(ps.stdout)

        memory = float(info["MemTotal"]) / (1024**3)
        print(
            INFO.format(
                version=opensafely.__version__,
                docker_version=info["ServerVersion"],
                memory=f"{memory:.1f}G",
                cpu=info["NCPU"],
            )
        )
    except Exception as exc:
        raise RuntimeError(f"Error retreiving docker information: {exc}")

    print("OpenSAFELY Docker image versions:")
    try:
        local_images = pull.get_local_images()
        updates = pull.check_version(local_images)
    except Exception as exc:
        raise RuntimeError(f"Error retreiving image information: {exc}")
    else:
        for image, sha in sorted(local_images.items()):
            update = "(needs update)" if image in updates else "(latest version)"
            print(f" - {image:24}: {sha[7:15]} {update}")

    return True
