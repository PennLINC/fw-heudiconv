#!/usr/bin/env python

"""Tests for `fw-heudiconv` package."""

import pytest
import sys
import flywheel

def test_init():
    print(sys.version)
    assert 1
    return

def test_client():

    client = flywheel.Client()
    assert client
    return 1
