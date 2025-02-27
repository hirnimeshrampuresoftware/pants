# Copyright 2020 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import annotations

import itertools

from pants.backend.python.goals.lockfile import PythonLockfileRequest, PythonToolLockfileSentinel
from pants.backend.python.subsystems.python_tool_base import PythonToolBase
from pants.backend.python.target_types import ConsoleScript, InterpreterConstraintsField
from pants.backend.python.util_rules.interpreter_constraints import InterpreterConstraints
from pants.base.specs import AddressSpecs, DescendantAddresses
from pants.engine.rules import Get, collect_rules, rule
from pants.engine.target import UnexpandedTargets
from pants.engine.unions import UnionRule
from pants.python.python_setup import PythonSetup
from pants.util.docutil import git_url
from pants.util.logging import LogLevel


class IPython(PythonToolBase):
    options_scope = "ipython"
    help = "The IPython enhanced REPL (https://ipython.org/)."

    default_version = "ipython==7.16.1"  # The last version to support Python 3.6.
    default_main = ConsoleScript("ipython")

    register_lockfile = True
    default_lockfile_resource = ("pants.backend.python.subsystems", "ipython_lockfile.txt")
    default_lockfile_path = "src/python/pants/backend/python/subsystems/ipython_lockfile.txt"
    default_lockfile_url = git_url(default_lockfile_path)

    @classmethod
    def register_options(cls, register):
        super().register_options(register)
        register(
            "--ignore-cwd",
            type=bool,
            advanced=True,
            default=True,
            help="Whether to tell IPython not to put the CWD on the import path.\n\n"
            "Normally you want this to be True, so that imports come from the hermetic "
            "environment Pants creates.\n\nHowever IPython<7.13.0 doesn't support this option, "
            "so if you're using an earlier version (e.g., because you have Python 2.7 code) "
            "then you will need to set this to False, and you may have issues with imports "
            "from your CWD shading the hermetic environment.",
        )


class IPythonLockfileSentinel(PythonToolLockfileSentinel):
    options_scope = IPython.options_scope


@rule(
    desc=(
        "Determine all Python interpreter versions used by iPython in your project (for lockfile "
        "usage)"
    ),
    level=LogLevel.DEBUG,
)
async def setup_ipython_lockfile(
    _: IPythonLockfileSentinel, ipython: IPython, python_setup: PythonSetup
) -> PythonLockfileRequest:
    if not ipython.uses_lockfile:
        return PythonLockfileRequest.from_tool(ipython)

    # IPython is often run against the whole repo (`./pants repl ::`), but it is possible to run
    # on subsets of the codebase with disjoint interpreter constraints, such as
    # `./pants repl py2::` and then `./pants repl py3::`. Still, even with those subsets possible,
    # we need a single lockfile that works with all possible Python interpreters in use.
    #
    # This ORs all unique interpreter constraints. The net effect is that every possible Python
    # interpreter used will be covered.
    all_build_targets = await Get(UnexpandedTargets, AddressSpecs([DescendantAddresses("")]))
    unique_constraints = {
        InterpreterConstraints.create_from_compatibility_fields(
            [tgt[InterpreterConstraintsField]], python_setup
        )
        for tgt in all_build_targets
        if tgt.has_field(InterpreterConstraintsField)
    }
    constraints = InterpreterConstraints(itertools.chain.from_iterable(unique_constraints))
    return PythonLockfileRequest.from_tool(
        ipython, constraints or InterpreterConstraints(python_setup.interpreter_constraints)
    )


def rules():
    return (*collect_rules(), UnionRule(PythonToolLockfileSentinel, IPythonLockfileSentinel))
