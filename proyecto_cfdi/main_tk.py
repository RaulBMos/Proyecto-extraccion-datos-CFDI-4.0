
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
import sys
import subprocess
import platform
from typing import Optional

# Importar lógica de negocio existente
try:
    from cfdi_tool.extractor import CFDIExtractor
    from cfdi_tool.excel_writer import exportar_a_excel
except ImportError as e:
    messagebox.showerror("Error de Importación", f"No se pudieron cargar los módulos del proyecto:\n{e}")
    sys.exit(1)

class CFDIApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Procesador CFDI → Excel")
        self.geometry("800x600")
        self.config(padx=20, pady=20)
        
        # Variables de estado
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.status_msg = tk.StringVar(value="Listo para iniciar")
        self.is_processing = False
        self.process_finished = False # Nuevo flag
        
        self.extractor = CFDIExtractor()
        
        self.create_widgets()
        
    def create_widgets(self):
        # Estilos
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Helvetica", 16, "bold"))
        style.configure("Header.TLabel", font=("Helvetica", 11, "bold"))
        
        # Título
        ttk.Label(self, text="Procesador de Facturas CFDI", style="Title.TLabel").pack(pady=(0, 20))
        
        # Frame Principal
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- SECCIÓN ENTRADA ---
        input_frame = ttk.LabelFrame(main_frame, text="Carpeta de Entrada (XMLs)", padding=10)
        input_frame.pack(fill=tk.X, pady=10)
        
        ttk.Entry(input_frame, textvariable=self.input_path, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(input_frame, text="Examinar...", command=self.browse_input).pack(side=tk.RIGHT)
        
        self.lbl_input_info = ttk.Label(input_frame, text="", foreground="gray")
        self.lbl_input_info.pack(side=tk.BOTTOM, anchor="w", pady=(5, 0))
        
        # --- SECCIÓN SALIDA ---
        output_frame = ttk.LabelFrame(main_frame, text="Carpeta de Salida (Excel)", padding=10)
        output_frame.pack(fill=tk.X, pady=10)
        
        ttk.Entry(output_frame, textvariable=self.output_path, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(output_frame, text="Examinar...", command=self.browse_output).pack(side=tk.RIGHT)
        
        # --- PROGRESO Y ACCIÓN ---
        action_frame = ttk.Frame(main_frame, padding=20)
        action_frame.pack(fill=tk.X, pady=10)
        
        self.btn_process = ttk.Button(action_frame, text="🚀 Iniciar Procesamiento", command=self.start_processing_thread, state="disabled")
        self.btn_process.pack(fill=tk.X, pady=(0, 10))
        
        self.progress = ttk.Progressbar(action_frame, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)
        
        ttk.Label(action_frame, textvariable=self.status_msg, anchor="center").pack(fill=tk.X)

        # --- LOG ---
        log_frame = ttk.LabelFrame(main_frame, text="Registro de Actividad (Log)", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.txt_log = scrolledtext.ScrolledText(log_frame, height=10, state='disabled', font=("Consolas", 9))
        self.txt_log.pack(fill=tk.BOTH, expand=True)
        
    def browse_input(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta con archivos XML")
        if folder:
            self.input_path.set(folder)
            self.validate_input(folder)
            self.process_finished = False # Resetear estado
            self.check_ready()
            
    def browse_output(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta de destino")
        if folder:
            self.output_path.set(folder)
            self.process_finished = False # Resetear estado
            self.check_ready()
            
    def validate_input(self, folder):
        try:
            files = [f for f in os.listdir(folder) if f.lower().endswith('.xml')]
            count = len(files)
            if count > 0:
                self.lbl_input_info.config(text=f"✅ Se encontraron {count} archivos XML", foreground="green")
            else:
                self.lbl_input_info.config(text="⚠️ No se encontraron archivos XML en esta carpeta", foreground="orange")
        except Exception as e:
            self.lbl_input_info.config(text=f"❌ Error al leer carpeta: {e}", foreground="red")
            
    def check_ready(self):
        if self.input_path.get() and self.output_path.get() and not self.is_processing and not self.process_finished:
            self.btn_process.config(state="normal")
        else:
            self.btn_process.config(state="disabled")
            
    def start_processing_thread(self):
        self.is_processing = True
        self.btn_process.config(state="disabled")
        self.progress['value'] = 0
        self.log_message("--- Iniciando Procesamiento ---", clear=True) # Limpiar log al iniciar
        
        # Ejecutar en hilo separado para no congelar la UI
        threading.Thread(target=self.run_processing, daemon=True).start()
        
    def run_processing(self):
        try:
            input_dir = self.input_path.get()
            output_dir = self.output_path.get()
            
            xml_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.xml')]
            total = len(xml_files)
            
            if total == 0:
                self.final_update("Error: No hay XMLs", error=True)
                return
            
            todos_los_datos = []
            errores = 0
            
            for i, filename in enumerate(xml_files):
                # Actualizar UI desde el hilo
                msg = f"Procesando {i+1}/{total}: {filename}"
                self.update_status(msg, (i / total) * 100)
                self.log_message_thread(f"Leyendo: {filename}")
                
                try:
                    full_path = os.path.join(input_dir, filename)
                    data = self.extractor.procesar_cfdi_completo(full_path)
                    if data:
                        todos_los_datos.append(data)
                        self.log_message_thread(f"   [OK] {filename}")
                    else:
                        errores += 1
                        self.log_message_thread(f"   [ERROR] No se extrajeron datos de {filename}")
                except Exception as e:
                    print(f"Error en {filename}: {e}")
                    self.log_message_thread(f"   [EXCEPCIÓN] {e} en {filename}")
                    errores += 1
            
            self.update_status("Generando Excel...", 100)
            self.log_message_thread("Generando archivo Excel...")
            
            if not todos_los_datos:
                self.final_update("No se extrajeron datos válidos", error=True)
                return
                
            output_file = os.path.join(output_dir, "reporte_cfdi.xlsx")
            exportar_a_excel(todos_los_datos, output_file)
            
            self.log_message_thread(f"Excel guardado en: {output_file}")
            self.log_message_thread(f"Resumen: Procesados={len(todos_los_datos)}, Errores={errores}")
            
            msg = f"¡Completado!\n\nProcesados: {len(todos_los_datos)}\nErrores: {errores}\n\nArchivo guardado en:\n{output_file}"
            self.final_update(msg, success=True, file_path=output_file)
            
        except Exception as e:
            self.log_message_thread(f"ERROR CRÍTICO: {e}")
            self.final_update(f"Error crítico: {e}", error=True)
            
    def update_status(self, message, progress_val):
        self.after(0, lambda: self._update_ui_safe(message, progress_val))
        
    def log_message_thread(self, message, clear=False):
        self.after(0, lambda: self.log_message(message, clear))

    def log_message(self, message, clear=False):
        self.txt_log.config(state='normal')
        if clear:
            self.txt_log.delete(1.0, tk.END)
        self.txt_log.insert(tk.END, message + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state='disabled')
        
    def _update_ui_safe(self, message, progress_val):
        self.status_msg.set(message)
        self.progress['value'] = progress_val
        
    def final_update(self, message, error=False, success=False, file_path=None):
        self.after(0, lambda: self._finish_process(message, error, success, file_path))
        
    def _finish_process(self, message, error, success, file_path):
        self.is_processing = False
        if success:
             self.process_finished = True # Dejamos el botón deshabilitado
        
        self.check_ready()
        self.status_msg.set("Proceso finalizado")
        
        if error:
            messagebox.showerror("Error", message)
        elif success:
            ask = messagebox.askyesno("Éxito", message + "\n\n¿Deseas abrir la carpeta de salida?")
            if ask and file_path:
                self.open_file(os.path.dirname(file_path))
                
    def open_file(self, path):
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

if __name__ == "__main__":
    app = CFDIApp()
    app.mainloop()
