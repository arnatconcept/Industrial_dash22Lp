import sqlite3
import pandas as pd

DB_PATH = 'db.sqlite3'
TABLE_NAME = 'api_equipo'

def connect_db():
    return sqlite3.connect(DB_PATH)

def show_menu():
    print("\n===== MENÚ DE GESTIÓN DE EQUIPOS =====")
    print("1. Ver todos los registros")
    print("2. Importar desde Excel (actualiza si el ID existe)")
    print("3. Exportar a Excel")
    print("4. Agregar nuevo registro")
    print("5. Editar un registro")
    print("6. Eliminar un registro")
    print("0. Salir")

def view_records(conn):
    df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)
    print(df)

def import_from_excel(conn):
    file = input("Ruta al archivo Excel: ")
    try:
        df = pd.read_excel(file)

        cursor = conn.cursor()
        updated, created = 0, 0

        for _, row in df.iterrows():
            record = tuple(row.values)
            placeholders = ', '.join(['?'] * len(record))
            columns = ', '.join(df.columns)
            updates = ', '.join([f"{col}=?" for col in df.columns if col != 'id'])

            # Comprobar si el ID ya existe
            cursor.execute(f"SELECT * FROM {TABLE_NAME} WHERE id = ?", (row['id'],))
            if cursor.fetchone():
                # Actualizar
                update_values = [row[col] for col in df.columns if col != 'id'] + [row['id']]
                cursor.execute(f"UPDATE {TABLE_NAME} SET {updates} WHERE id = ?", update_values)
                updated += 1
            else:
                # Insertar
                cursor.execute(f"INSERT INTO {TABLE_NAME} ({columns}) VALUES ({placeholders})", record)
                created += 1

        conn.commit()
        print(f"Importación completa. {created} creados, {updated} actualizados.")

    except Exception as e:
        print("Error al importar:", e)

def export_to_excel(conn):
    df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)
    file = input("Nombre del archivo Excel a guardar (ej. motores.xlsx): ")
    df.to_excel(file, index=False)
    print(f"Exportado exitosamente a {file}")

def add_record(conn):
    cursor = conn.cursor()
    df = pd.read_sql_query(f"PRAGMA table_info({TABLE_NAME})", conn)
    values = []
    for column in df['name']:
        if column == 'id':
            continue
        val = input(f"Ingrese valor para '{column}': ")
        values.append(val)
    columns = ', '.join(df['name'][1:])
    placeholders = ', '.join(['?'] * len(values))
    cursor.execute(f"INSERT INTO {TABLE_NAME} ({columns}) VALUES ({placeholders})", values)
    conn.commit()
    print("Registro agregado exitosamente.")

def edit_record(conn):
    record_id = input("ID del registro a editar: ")
    cursor = conn.cursor()

    df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME} WHERE id = ?", conn, params=(record_id,))
    if df.empty:
        print("Registro no encontrado.")
        return

    print("Valores actuales:")
    print(df.to_string(index=False))

    updated_values = {}
    for col in df.columns:
        if col == 'id':
            continue
        current_value = df[col].values[0]
        new_val = input(f"{col} (actual: {current_value}) -> Nuevo valor (Enter para mantener): ")
        if new_val != '':
            updated_values[col] = new_val

    if updated_values:
        set_clause = ', '.join([f"{k} = ?" for k in updated_values.keys()])
        values = list(updated_values.values()) + [record_id]
        cursor.execute(f"UPDATE {TABLE_NAME} SET {set_clause} WHERE id = ?", values)
        conn.commit()
        print("Registro actualizado.")
    else:
        print("No se hicieron cambios.")

def delete_record(conn):
    record_id = input("ID del registro a eliminar: ")
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE id = ?", (record_id,))
    conn.commit()
    print("Registro eliminado.")

def main():
    conn = connect_db()
    while True:
        show_menu()
        option = input("Seleccione una opción: ")

        if option == '1':
            view_records(conn)
        elif option == '2':
            import_from_excel(conn)
        elif option == '3':
            export_to_excel(conn)
        elif option == '4':
            add_record(conn)
        elif option == '5':
            edit_record(conn)
        elif option == '6':
            delete_record(conn)
        elif option == '0':
            print("Saliendo del programa.")
            break
        else:
            print("Opción inválida.")

    conn.close()

if __name__ == "__main__":
    main()
