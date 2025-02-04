DESCRIPTION = "DEPRECATED. Use: opensafely launch rstudio"

add_arguments = lambda _: None


def main(*args, **kwargs):
    print(
        "opensafely rstudio command is deprecated - instead use: opensafely launch rstudio"
    )
    return 1
