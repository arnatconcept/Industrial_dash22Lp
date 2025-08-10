import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox

class LineStructureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Line Structure Viewer")
        self.root.geometry("900x700")
        
        # Create main container
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # File selection
        self.file_frame = ttk.LabelFrame(self.main_frame, text="1. Select Data File", padding=10)
        self.file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(self.file_frame, text="Browse...", command=self.load_file).pack(side=tk.LEFT)
        self.file_path = tk.StringVar()
        ttk.Label(self.file_frame, textvariable=self.file_path, wraplength=600).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Tree view
        self.tree_frame = ttk.LabelFrame(self.main_frame, text="2. Line Structure", padding=10)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create tree with scrollbars
        self.tree = ttk.Treeview(self.tree_frame)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        y_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=y_scroll.set)
        
        # Configure tree columns
        self.tree["columns"] = ("type")
        self.tree.column("#0", width=300, minwidth=200, stretch=tk.YES)
        self.tree.column("type", width=100, minwidth=50, stretch=tk.NO)
        
        self.tree.heading("#0", text="Name", anchor=tk.W)
        self.tree.heading("type", text="Type", anchor=tk.W)
        
        # Status bar
        self.status = tk.StringVar()
        self.status.set("Ready to load data file")
        ttk.Label(self.main_frame, textvariable=self.status, relief=tk.SUNKEN).pack(fill=tk.X, pady=5)
        
        # Data storage
        self.data = None
        self.line_structure = {}
    
    def load_file(self):
        filepath = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                # Read data based on file extension
                if filepath.endswith('.csv'):
                    self.data = pd.read_csv(filepath)
                else:
                    self.data = pd.read_excel(filepath)
                
                self.file_path.set(filepath)
                self.status.set(f"Loaded {len(self.data)} records from {filepath}")
                self.process_data()
                self.display_structure()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")
                self.status.set("Error loading file")
    
    def process_data(self):
        # Clear existing structure
        self.line_structure = {}
        
        # Group data by Line and Sector
        for _, row in self.data.iterrows():
            line = row['Línea']
            sector = row['Sector']
            equipment = row['Equipo']
            
            # Skip empty rows
            if pd.isna(line) or pd.isna(sector) or pd.isna(equipment):
                continue
            
            # Initialize line if not exists
            if line not in self.line_structure:
                self.line_structure[line] = {}
            
            # Initialize sector if not exists
            if sector not in self.line_structure[line]:
                self.line_structure[line][sector] = []
            
            # Add equipment to sector
            self.line_structure[line][sector].append(equipment)
    
    def display_structure(self):
        # Clear existing tree
        self.tree.delete(*self.tree.get_children())
        
        # Add lines as top-level items
        for line in sorted(self.line_structure.keys()):
            line_node = self.tree.insert("", "end", text=f"Línea: {line}", values=("Line",))
            
            # Add sectors under each line
            for sector in sorted(self.line_structure[line].keys()):
                sector_node = self.tree.insert(line_node, "end", text=f"Sector: {sector}", values=("Sector",))
                
                # Add equipment under each sector
                for equipment in sorted(self.line_structure[line][sector]):
                    self.tree.insert(sector_node, "end", text=equipment, values=("Equipment",))
        
        # Expand all items by default
        for child in self.tree.get_children():
            self.tree.item(child, open=True)
        
        self.status.set(f"Displaying structure with {len(self.line_structure)} lines")

if __name__ == "__main__":
    root = tk.Tk()
    app = LineStructureApp(root)
    root.mainloop()