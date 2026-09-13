from dataclasses import fields


def transform(table, register_cls, table_cls, field_map):
    registers = []
    for source in table.registers:
        kwargs = {
            field_map.get(field.name, field.name): getattr(source, field.name)
            for field in fields(source)
        }
        registers.append(register_cls(**kwargs))
    return table_cls(registers=registers)
