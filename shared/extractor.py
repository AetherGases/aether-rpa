def extract(connection, query, register_cls, table_cls):
    cursor = connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    registers = [
        register_cls(
            **{cursor.description[i][0]: value for i, value in enumerate(row)}
        )
        for row in rows
    ]
    return table_cls(registers=registers)
