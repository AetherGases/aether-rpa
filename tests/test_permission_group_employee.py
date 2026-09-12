from permission_group_employee import Register, Table


def test_register_and_table_hold_permission_group_employee_fields() -> None:
    register = Register(id_employee=1, id_permission_group=2)
    table = Table(registers=[register])

    assert table.registers == [register]
    assert register.id_employee == 1
    assert register.id_permission_group == 2
    assert not hasattr(register, "id")


def test_table_accepts_empty_registers() -> None:
    table = Table(registers=[])

    assert table.registers == []
