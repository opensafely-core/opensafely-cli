class ProjectValidationError(Exception):
    pass


class InvalidPatternError(ProjectValidationError):
    pass


class YAMLError(Exception):
    pass
