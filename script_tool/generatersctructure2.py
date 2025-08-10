import pandas as pd
from collections import defaultdict

def generate_structure_files(data_path):
    # Load the original data
    df = pd.read_excel(data_path)  # Change to pd.read_csv() if using CSV
    
    # 1. Generate estrucsectores.xlsx (Sectors)
    # Mapeo de líneas a IDs
    line_mapping = {
        'L1': 1,
        'L2': 2,
        'PE': 3
    }
    
    # Get unique sector-line pairs and create sector mapping
    sector_line_pairs = df[['Sector', 'Línea']].drop_duplicates().dropna()
    
    # Create sectors data with IDs and build sector name to ID mapping
    sectors = []
    sector_name_to_id = {}  # Diccionario para mapear nombre de sector a ID
    line_name_to_id = {}    # Diccionario para mapear nombre de línea a ID
    
    for idx, (sector, line) in enumerate(sector_line_pairs.iterrows(), start=1):
        sector_name = sector_line_pairs.at[sector, 'Sector']
        line_value = str(sector_line_pairs.at[sector, 'Línea']).strip().upper()
        line_id = line_mapping.get(line_value, line_value)
        
        sectors.append({
            'id': idx,
            'nombre': sector_name,
            'linea_id': line_id
        })
        sector_name_to_id[sector_name] = idx  # Guardar mapeo nombre -> ID
        line_name_to_id[line_value] = line_id  # Guardar mapeo línea -> ID
    
    sectors_df = pd.DataFrame(sectors)
    
    # 2. Generate estrucequipos.xlsx (Equipment)
    equipment = []
    equipment_name_to_id = {}  # Diccionario para mapear nombre de equipo a ID
    equipment_id = 1
    
    # Create equipment data with sector IDs instead of names
    for _, row in df.iterrows():
        if pd.notna(row['Equipo']) and pd.notna(row['Sector']):
            sector_name = row['Sector']
            sector_id = sector_name_to_id.get(sector_name)
            equipo_name = row['Equipo']
            
            if sector_id:
                equipment.append({
                    'id': equipment_id,
                    'nombre': equipo_name,
                    'sector_id': sector_id
                })
                # Guardar mapeo (equipo_name, sector_id) -> equipment_id
                equipment_name_to_id[(equipo_name, sector_id)] = equipment_id
                equipment_id += 1
    
    equipment_df = pd.DataFrame(equipment).drop_duplicates(subset=['nombre', 'sector_id'])
    
    # 3. Generate estrucmotors.xlsx (Motors)
    motors = []
    motor_id = 1
    
    # Procesar cada motor del archivo original
    for _, row in df.iterrows():
        if pd.notna(row.get('ID')):  # Usamos ID como identificador de motor
            sector_name = row['Sector']
            equipo_name = row['Equipo']
            linea_value = str(row['Línea']).strip().upper() if pd.notna(row['Línea']) else None
            
            sector_id = sector_name_to_id.get(sector_name)
            equipo_id = equipment_name_to_id.get((equipo_name, sector_id)) if sector_id else None
            linea_id = line_name_to_id.get(linea_value) if linea_value else None
            
            if sector_id and equipo_id and linea_id:
                motor_data = {
                    'id': motor_id,
                    'codigo': row['ID'],
                    'modelo': row['Modelo'],
                    'marca': row['Marca'],
                    'equipo_id': equipo_id,
                    'sector_id': sector_id,
                    'linea_id': linea_id, 
                    'carcasa': row['Carcasa'],
                    'freno': row['Freno'],
                    'brida': row['Brida'],
                    'potencia': row['Potencia'],
                    'anclaje': row['Anclaje'],
                    'rpm': row['RPM'],
                    'estado': row['Estado'],
                    'ubicacion': row['Ubicación'],
                    'fecha_ingreso': row['Fecha de Ingreso'],
                    'observaciones': row['Observaciones'],
                    'stock': row['Stock']
                }
                
                # Convertir NaN a None para limpieza
                motor_data = {k: (v if pd.notna(v) else None) for k, v in motor_data.items()}
                motors.append(motor_data)
                motor_id += 1
    
    motors_df = pd.DataFrame(motors)
    
    # Save to Excel files
    with pd.ExcelWriter('estrucsectores.xlsx') as writer:
        sectors_df.to_excel(writer, sheet_name='Sectores', index=False)
    
    with pd.ExcelWriter('estrucequipos.xlsx') as writer:
        equipment_df.to_excel(writer, sheet_name='Equipos', index=False)
    
    with pd.ExcelWriter('estrucmotors.xlsx') as writer:
        motors_df.to_excel(writer, sheet_name='Motores', index=False)
    
    print(f"Generated estrucsectores.xlsx with {len(sectors_df)} sectors")
    print(f"Generated estrucequipos.xlsx with {len(equipment_df)} equipment entries")
    print(f"Generated estrucmotors.xlsx with {len(motors_df)} motor entries")
    print("\nRelación de Sectores creados:")
    print(sectors_df[['id', 'nombre', 'linea_id']].to_string(index=False))
    print("\nRelación de Equipos creados:")
    print(equipment_df[['id', 'nombre', 'sector_id']].to_string(index=False))

# Resto del código (GUI) permanece igual
class StructureGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Structure File Generator")
        self.root.geometry("600x300")
        
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(self.main_frame, text="Generate Structure Files", font=('Arial', 14)).pack(pady=10)
        
        ttk.Button(self.main_frame, text="Select Input File", 
                  command=self.select_file).pack(pady=10)
        
        self.file_label = ttk.Label(self.main_frame, text="No file selected")
        self.file_label.pack(pady=5)
        
        ttk.Button(self.main_frame, text="Generate Files", 
                  command=self.generate_files, state=tk.DISABLED).pack(pady=20)
        self.generate_btn = self.root.nametowidget(self.main_frame.winfo_children()[-1])
        
        self.status = ttk.Label(self.main_frame, text="Ready")
        self.status.pack()
        
        self.file_path = None
    
    def select_file(self):
        filepath = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filepath:
            self.file_path = filepath
            self.file_label.config(text=os.path.basename(filepath))
            self.generate_btn.config(state=tk.NORMAL)
            self.status.config(text="File selected - ready to generate")
    
    def generate_files(self):
        if self.file_path:
            try:
                generate_structure_files(self.file_path)
                self.status.config(text="Files generated successfully!", foreground='green')
            except Exception as e:
                self.status.config(text=f"Error: {str(e)}", foreground='red')
        else:
            self.status.config(text="No file selected", foreground='red')

if __name__ == "__main__":
    import tkinter as tk
    from tkinter import ttk, filedialog
    import os
    
    root = tk.Tk()
    app = StructureGeneratorApp(root)
    root.mainloop()