import importlib


def test_package_exports_main():
    package = importlib.import_module("first_agent_project")

    assert hasattr(package, "main")
    assert callable(package.main)
