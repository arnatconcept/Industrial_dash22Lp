import sqlite3

DB_PATH = "db.sqlite3"

def connect_db():
    return sqlite3.connect(DB_PATH)

def list_tables(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    return [row[0] for row in cursor.fetchall()]

def list_columns(conn, table):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table});")
    return [(col[1], col[2]) for col in cursor.fetchall()]  # (name, type)

def show_records(conn, table):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    print("\n--- Registros ---")
    for row in rows:
        print(dict(zip(columns, row)))
    return rows, columns

def insert_record(conn, table):
    columns = list_columns(conn, table)
    values = []
    print(f"\n--- Ingresando nuevo registro en {table} ---")
    for col, typ in columns:
        if col == "id":
            values.append(None)
            continue
        val = input(f"{col} ({typ}): ")
        values.append(val if val != "" else None)
    placeholders = ",".join(["?"] * len(columns))
    conn.execute(f"INSERT INTO {table} VALUES ({placeholders})", values)
    conn.commit()
    print("Registro insertado correctamente.")

def edit_record(conn, table):
    rows, columns = show_records(conn, table)
    id_col = columns[0]
    record_id = input(f"\nIngrese el valor de '{id_col}' del registro a editar: ")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table} WHERE {id_col}=?", (record_id,))
    row = cursor.fetchone()
    if not row:
        print("Registro no encontrado.")
        return
    print(f"\n--- Editando registro ID {record_id} ---")
    new_values = []
    for idx, col in enumerate(columns):
        if col == id_col:
            new_values.append(row[idx])
            continue
        current_val = row[idx]
        new_val = input(f"{col} (actual: {current_val}) → Nuevo valor (dejar vacío para mantener): ")
        new_values.append(new_val if new_val != "" else current_val)
    set_clause = ", ".join([f"{col}=?" for col in columns if col != id_col])
    conn.execute(f"UPDATE {table} SET {set_clause} WHERE {id_col}=?", (*new_values[1:], record_id))
    conn.commit()
    print("Registro actualizado.")

def delete_record(conn, table):
    rows, columns = show_records(conn, table)
    id_col = columns[0]
    record_id = input(f"\nIngrese el valor de '{id_col}' del registro a eliminar: ")
    confirm = input("¿Está seguro de que desea eliminar este registro? (s/n): ")
    if confirm.lower() == "s":
        conn.execute(f"DELETE FROM {table} WHERE {id_col}=?", (record_id,))
        conn.commit()
        print("Registro eliminado.")
    else:
        print("Cancelado.")

def main_menu():
    conn = connect_db()
    while True:
        print("\n===== MENÚ BASE DE DATOS =====")
        print("1. Listar tablas")
        print("2. Ver registros de una tabla")
        print("3. Insertar registro")
        print("4. Editar registro")
        print("5. Eliminar registro")
        print("6. Salir")
        option = input("Seleccione una opción: ")

        if option == "1":
            tables = list_tables(conn)
            print("\nTablas encontradas:")
            for t in tables:
                print(f"• {t}")
        elif option in ["2", "3", "4", "5"]:
            tables = list_tables(conn)
            print("\nTablas disponibles:")
            for idx, t in enumerate(tables):
                print(f"{idx + 1}. {t}")
            try:
                idx = int(input("Seleccione el número de tabla: ")) - 1
                table = tables[idx]
            except:
                print("Selección inválida.")
                continue

            if option == "2":
                show_records(conn, table)
            elif option == "3":
                insert_record(conn, table)
            elif option == "4":
                edit_record(conn, table)
            elif option == "5":
                delete_record(conn, table)
        elif option == "6":
            print("Saliendo...")
            break
        else:
            print("Opción no válida. Intente nuevamente.")
    conn.close()

if __name__ == "__main__":
    main_menu()
