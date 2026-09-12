import importlib

import pytest

TABLE_PACKAGES = [
    "address",
    "enterprise",
    "unit",
    "department",
    "storage_file",
    "permission_group",
    "permission",
    "permission_group_permission",
    "employee",
    "permission_group_employee",
    "plan",
    "plan_subscription",
]


@pytest.mark.parametrize("package", TABLE_PACKAGES)
def test_package_exports_register_and_table(package: str) -> None:
    module = importlib.import_module(package)

    assert module.Register is not None
    assert module.Table is not None
    assert module.__all__ == ["Register", "Table"] or (
        package == "employee" and module.__all__ == ["EmployeeStatus", "Register", "Table"]
    )


@pytest.mark.parametrize("package", TABLE_PACKAGES)
def test_etl_modules_are_importable(package: str) -> None:
    importlib.import_module(f"{package}.extractor")
    importlib.import_module(f"{package}.transformer")
    importlib.import_module(f"{package}.driver")
