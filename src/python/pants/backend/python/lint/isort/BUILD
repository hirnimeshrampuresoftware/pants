# Copyright 2019 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

python_library(dependencies=[":lockfile"])
resources(name="lockfile", sources=["lockfile.txt"])

python_tests(
    name="rules_integration_test",
    sources=["rules_integration_test.py"],
    timeout=120,
    # We want to make sure the default lockfile works for both macOS and Linux.
    tags=["platform_specific_behavior"],
)
