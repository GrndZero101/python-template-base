"""Setup shared by every test in this repo."""

import os

from plumbum import local

# Git's variables that tie a command to one repository, as `git rev-parse --local-env-vars` lists
# them. A git hook exports GIT_INDEX_FILE=.git/index, so when the commit runs generation-tests,
# every git command the suite starts inherits it. copier runs `git --git-dir=<clone>` from this
# repo's root, which then stages the clone's objects into THIS repo's index, leaving it pointing at
# blobs it does not have (2026-10-18: "invalid object ... for 'TODO.md'", and a failed commit).
GIT_REPOSITORY_VARIABLES = (
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CONFIG",
    "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_COUNT",
    "GIT_OBJECT_DIRECTORY",
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_IMPLICIT_WORK_TREE",
    "GIT_GRAFT_FILE",
    "GIT_INDEX_FILE",
    "GIT_NO_REPLACE_OBJECTS",
    "GIT_REPLACE_REF_BASE",
    "GIT_PREFIX",
    "GIT_SHALLOW_FILE",
    "GIT_COMMON_DIR",
)


def pytest_configure() -> None:
    """Drop the variables a git hook set, so no git command here can reach the hook's repository.

    From plumbum's environment too: copier runs git through plumbum, which copied `os.environ` when
    pytest-copie, a plugin, imported it, before any conftest ran.
    """
    for name in GIT_REPOSITORY_VARIABLES:
        os.environ.pop(name, None)
        if name in local.env:
            del local.env[name]
