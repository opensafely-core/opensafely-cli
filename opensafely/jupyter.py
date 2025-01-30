from opensafely import launch


DESCRIPTION = "DEPRECATED. Use: opensafely launch jupyter"

add_arguments = launch.add_base_args


def main(directory, name, port, no_browser):
    print(
        "opensafely jupyter command is deprecated - instead use: opensafely launch jupyter"
    )
    return launch.main("jupyter", directory, name, port, no_browser)
