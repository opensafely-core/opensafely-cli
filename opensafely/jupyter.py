DESCRIPTION = "DEPRECATED. Use: opensafely launch jupyter"

add_arguments = lambda _: None


def main(*args, **kwargs):
    print(
        "opensafely jupyter command is deprecated - instead use: opensafely launch jupyter"
    )
    return 1
