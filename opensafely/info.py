import json
import subprocess
import sys

import opensafely
from opensafely import pull


DESCRIPTION = "Print information about the opensafely tool and available resources"


def add_arguments(parser):
    pass


INFO = """
opensafely version: {version}
docker version: {docker_version}
docker memory: {memory}
docker cpu: {cpu}
"""


def main():
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
    except Exception:
        sys.exit("Error retreiving docker information")

    print("OpenSAFELY Docker image versions:")
    try:
        local_images = pull.get_local_images()
        updates = pull.check_version(local_images)
    except Exception:
        sys.exit("Error retreiving image information")
    else:
        for image, sha in sorted(local_images.items()):
            update = "(needs update)" if image in updates else "(latest version)"
            print(f" - {image:24}: {sha[7:15]} {update}")
