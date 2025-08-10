import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import os

class MotorFilterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Motor Filter Application")
        self.root.geometry("1000x700")
        
        # Configure styles
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        self.style.configure('TButton', font=('Arial', 10), padding=5)
        self.style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        
        # Data storage
        self.df = None
        self.filtered_df = None
        self.current_filters = {}
        
        # Create UI
        self.create_widgets()
        
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="1. Select Excel File", padding=10)
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(file_frame, text="Browse...", command=self.load_file).pack(side=tk.LEFT, padx=5)
        self.file_path = tk.StringVar()
        ttk.Label(file_frame, textvariable=self.file_path, wraplength=600).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Filter section
        filter_frame = ttk.LabelFrame(main_frame, text="2. Apply Filters", padding=10)
        filter_frame.pack(fill=tk.X, pady=5)
        
        # Filter controls
        control_frame = ttk.Frame(filter_frame)
        control_frame.pack(fill=tk.X)
        
        # Column selection
        ttk.Label(control_frame, text="Filter by:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.filter_column = ttk.Combobox(control_frame, state="readonly")
        self.filter_column.grid(row=0, column=1, padx=5, sticky=tk.W)
        self.filter_column.bind("<<ComboboxSelected>>", self.update_filter_values)
        
        # Value selection
        ttk.Label(control_frame, text="Value:").grid(row=0, column=2, padx=5, sticky=tk.W)
        self.filter_value = ttk.Combobox(control_frame)
        self.filter_value.grid(row=0, column=3, padx=5, sticky=tk.W)
        
        # Add filter button
        ttk.Button(control_frame, text="Add Filter", command=self.add_filter).grid(row=0, column=4, padx=5)
        
        # Current filters display
        ttk.Label(filter_frame, text="Current Filters:").pack(anchor=tk.W)
        self.filters_display = ScrolledText(filter_frame, height=4, wrap=tk.WORD)
        self.filters_display.pack(fill=tk.X)
        self.filters_display.config(state=tk.DISABLED)
        
        # Action buttons
        button_frame = ttk.Frame(filter_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Apply Filters", command=self.apply_filters).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Filters", command=self.clear_filters).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export Results", command=self.export_results).pack(side=tk.RIGHT, padx=5)
        
        # Results section
        results_frame = ttk.LabelFrame(main_frame, text="3. Filter Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for results
        self.tree = ttk.Treeview(results_frame)
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Status bar
        self.status = tk.StringVar()
        self.status.set("Ready")
        ttk.Label(main_frame, textvariable=self.status, relief=tk.SUNKEN).pack(fill=tk.X, pady=5)
    
    def load_file(self):
        filepath = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                self.df = pd.read_excel(filepath)
                self.file_path.set(filepath)
                self.update_column_list()
                self.display_data(self.df)
                self.status.set(f"Loaded {len(self.df)} records from {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")
                self.status.set("Error loading file")
    
    def update_column_list(self):
        if self.df is not None:
            columns = [col for col in self.df.columns if col != "ID"]
            self.filter_column['values'] = columns
            if columns:
                self.filter_column.current(0)
                self.update_filter_values()
    
    def update_filter_values(self, event=None):
        if self.df is not None and self.filter_column.get():
            col = self.filter_column.get()
            unique_values = self.df[col].dropna().unique()
            self.filter_value['values'] = sorted(unique_values)
    
    def add_filter(self):
        if self.df is None:
            messagebox.showwarning("Warning", "Please load a file first")
            return
            
        column = self.filter_column.get()
        value = self.filter_value.get()
        
        if not column or not value:
            messagebox.showwarning("Warning", "Please select both a column and a value")
            return
            
        self.current_filters[column] = value
        self.update_filters_display()
    
    def update_filters_display(self):
        self.filters_display.config(state=tk.NORMAL)
        self.filters_display.delete(1.0, tk.END)
        
        if not self.current_filters:
            self.filters_display.insert(tk.END, "No filters applied")
        else:
            for col, val in self.current_filters.items():
                self.filters_display.insert(tk.END, f"{col} = {val}\n")
        
        self.filters_display.config(state=tk.DISABLED)
    
    def apply_filters(self):
        if self.df is None:
            messagebox.showwarning("Warning", "Please load a file first")
            return
            
        if not self.current_filters:
            self.filtered_df = self.df.copy()
            messagebox.showinfo("Info", "No filters applied - showing all records")
        else:
            self.filtered_df = self.df.copy()
            for col, val in self.current_filters.items():
                # Handle numeric columns differently
                if pd.api.types.is_numeric_dtype(self.filtered_df[col]):
                    try:
                        val_num = float(val)
                        self.filtered_df = self.filtered_df[self.filtered_df[col] == val_num]
                    except ValueError:
                        self.filtered_df = self.filtered_df[self.filtered_df[col].astype(str).str.contains(val, na=False)]
                else:
                    self.filtered_df = self.filtered_df[self.filtered_df[col].astype(str).str.contains(val, na=False)]
        
        self.display_data(self.filtered_df)
        self.status.set(f"Showing {len(self.filtered_df)} of {len(self.df)} records")
    
    def clear_filters(self):
        self.current_filters = {}
        self.update_filters_display()
        if self.df is not None:
            self.display_data(self.df)
            self.status.set(f"Showing all {len(self.df)} records (filters cleared)")
    
    def display_data(self, df):
        # Clear existing data
        self.tree.delete(*self.tree.get_children())
        
        if df is None or df.empty:
            return
            
        # Set up columns
        self.tree["columns"] = list(df.columns)
        self.tree.column("#0", width=0, stretch=tk.NO)
        
        for col in df.columns:
            self.tree.column(col, anchor=tk.W, width=100)
            self.tree.heading(col, text=col, anchor=tk.W)
        
        # Add data
        for _, row in df.iterrows():
            self.tree.insert("", tk.END, values=list(row))
    
    def export_results(self):
        if self.filtered_df is None or self.filtered_df.empty:
            messagebox.showwarning("Warning", "No data to export")
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Save Filtered Results As"
        )
        
        if filepath:
            try:
                self.filtered_df.to_excel(filepath, index=False)
                messagebox.showinfo("Success", f"Results exported to:\n{filepath}")
                self.status.set(f"Exported {len(self.filtered_df)} records to {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export:\n{str(e)}")
                self.status.set("Export failed")

if __name__ == "__main__":
    root = tk.Tk()
    app = MotorFilterApp(root)
    root.mainloop()