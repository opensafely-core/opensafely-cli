from opensafely import launch


DESCRIPTION = "DEPRECATED. Use: opensafely launch rstudio"

add_arguments = launch.add_base_args


def main(directory, name, port, no_browser):
    print(
        "opensafely rstudio command is deprecated - instead use: opensafely launch rstudio"
    )
    return launch.main("rstudio", directory, name, port, no_browser)
