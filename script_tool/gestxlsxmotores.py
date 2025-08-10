import pandas as pd

# 1. Cargar ambos archivos Excel
df_motores = pd.read_excel("motores-v1.xlsx")  # Tabla original con todos los motores (ID, Modelo, Marca, Equipo, etc.)
df_actual = pd.read_excel("motores.xlsx")  # Tu Excel actual (con equipo_id, codigo, etc.)

# 2. Crear clave única para matching (combinando Marca + Modelo + Equipo + RPM)
df_motores["clave"] = (
    df_motores["codigo"].fillna("") + "_" + 
    df_motores["Equipo"].fillna("") + "_" +
    df_actual["Potencia"].fillna("") + "_" +
    df_actual["Brida"].fillna("") + "_" +
    df_actual["Anclaje"].fillna("") + "_" +    
    df_motores["RPM"].astype(str)
)

df_actual["clave"] = (
    df_actual["codigo"].fillna("") + "_" + 
    df_actual["equipo"].fillna("") + "_" +
    df_actual["potencia"].fillna("") + "_" +
    df_actual["brida"].fillna("") + "_" +
    df_actual["anclaje"].fillna("") + "_" +    
    df_actual["rpm"].astype(str)
)

# 3. Hacer merge para asignar IDs
df_final = pd.merge(
    df_actual,
    df_motores[["ID", "clave"]],  # Solo necesitamos el ID y la clave
    on="clave",
    how="left"
)

# 4. Renombrar columnas y guardar
df_final = df_final.rename(columns={"ID": "motor_id"})
df_final.to_excel("asignacion_motores_final.xlsx", index=False)

print("Archivo generado: 'asignacion_motores_final.xlsx'")
print(f"Motores asignados: {df_final['motor_id'].notna().sum()} de {len(df_actual)}")