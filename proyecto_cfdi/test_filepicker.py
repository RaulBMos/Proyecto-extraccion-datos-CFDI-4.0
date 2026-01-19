"""
main.py - Interfaz Gráfica para Procesador CFDI
"""

import flet as ft
import os
import asyncio
import subprocess
import platform
from typing import Optional
from cfdi_tool.extractor import CFDIExtractor

try:
    from cfdi_tool.excel_writer import exportar_a_excel
except ImportError:
    exportar_a_excel = None


class CFDIProcessorApp:
    """Aplicación GUI principal para procesamiento de CFDI."""

    def __init__(self, page: ft.Page):
        self.page = page
        
        # Variables de estado
        self.carpeta_input: Optional[str] = None
        self.carpeta_output: Optional[str] = None
        self.extractor = CFDIExtractor()
        
        # Componentes UI
        self.txt_input = ft.TextField(
            label="Ruta de la carpeta con archivos XML",
            hint_text=r"Ejemplo: C:\Users\tu_usuario\Documents\xmls",
            on_change=self.on_input_changed,
            expand=True
            
        )
        
        self.txt_output = ft.TextField(
            label="Ruta de la carpeta de salida",
            hint_text=r"Ejemplo: C:\Users\tu_usuario\Documents\salida",
            on_change=self.on_output_changed,
            expand=True
        )
        
        self.btn_procesar = ft.Button(
            "🚀 Iniciar Procesamiento",
            on_click=self.process_files,
            disabled=True,
            style=ft.ButtonStyle(
                color="white",
                bgcolor={ft.ControlState.DISABLED: "grey", "": "blue"},
                padding=20,
            ),
            width=300,
            height=50
        )
        
        self.progress_bar = ft.ProgressBar(width=500, visible=False, color="blue")
        self.txt_status = ft.Text("", visible=False, size=14, color="grey")
        self.container_resultado = ft.Container(visible=False)
        
        # Configurar página
        self.page.title = "Procesador CFDI → Excel"
        self.page.window_width = 900
        self.page.window_height = 700
        self.page.padding = 40
        self.page.theme_mode = ft.ThemeMode.LIGHT

    def build_ui(self):
        """Construye la interfaz completa."""
        return ft.Column(
            controls=[
                ft.Text(
                    "Procesador de Facturas CFDI", 
                    size=32, 
                    weight=ft.FontWeight.BOLD, 
                    color="blue"
                ),
                ft.Text(
                    "Convierte archivos XML CFDI a formato Excel",
                    size=16,
                    color="grey"
                ),
                ft.Divider(height=30),
                
                # Input Section
                ft.Text("📁 Carpeta de Entrada", size=18, weight=ft.FontWeight.BOLD),
                self.txt_input,
                
                ft.Divider(height=20),
                
                # Output Section
                ft.Text("💾 Carpeta de Salida", size=18, weight=ft.FontWeight.BOLD),
                self.txt_output,
                
                ft.Divider(height=40),
                
                # Process Button
                ft.Row(
                    controls=[self.btn_procesar],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                
                ft.Divider(height=30),
                
                # Progress Area
                ft.Column(
                    controls=[
                        self.txt_status,
                        self.progress_bar
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10
                ),
                
                ft.Divider(height=20),
                
                # Results Area
                self.container_resultado
            ],
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

    def on_input_changed(self, e):
        """Cuando el usuario escribe la ruta de entrada."""
        ruta = e.control.value.strip().strip('"')  # Quitar comillas si las pega
        
        if not ruta:
            self.carpeta_input = None
            e.control.error_text = None
            e.control.helper_text = None
            self.check_enable_process_button()
            self.page.update()
            return
        
        if os.path.exists(ruta) and os.path.isdir(ruta):
            try:
                archivos = [f for f in os.listdir(ruta) if f.lower().endswith('.xml')]
                if archivos:
                    self.carpeta_input = ruta
                    e.control.error_text = None
                    e.control.helper_text = f"✅ {len(archivos)} archivos XML encontrados"
                else:
                    self.carpeta_input = None
                    e.control.error_text = "⚠️ No se encontraron archivos XML en esta carpeta"
            except Exception as ex:
                self.carpeta_input = None
                e.control.error_text = f"❌ Error: {str(ex)}"
        else:
            self.carpeta_input = None
            e.control.error_text = "❌ La carpeta no existe o no es válida"
        
        self.check_enable_process_button()
        self.page.update()

    def on_output_changed(self, e):
        """Cuando el usuario escribe la ruta de salida."""
        ruta = e.control.value.strip().strip('"')
        
        if not ruta:
            self.carpeta_output = None
            e.control.error_text = None
            e.control.helper_text = None
            self.check_enable_process_button()
            self.page.update()
            return
        
        try:
            if not os.path.exists(ruta):
                os.makedirs(ruta)
                e.control.helper_text = "✅ Carpeta creada correctamente"
                e.control.error_text = None
            else:
                e.control.helper_text = "✅ Carpeta válida"
                e.control.error_text = None
            
            self.carpeta_output = ruta
        except Exception as ex:
            self.carpeta_output = None
            e.control.error_text = f"❌ Error: {str(ex)}"
        
        self.check_enable_process_button()
        self.page.update()

    def check_enable_process_button(self):
        """Habilita botón si ambas carpetas están seleccionadas."""
        self.btn_procesar.disabled = not (self.carpeta_input and self.carpeta_output)

    async def process_files(self, e):
        """Procesa archivos XML de forma asíncrona."""
        # Preparar UI
        self.btn_procesar.disabled = True
        self.progress_bar.visible = True
        self.progress_bar.value = None
        self.txt_status.visible = True
        self.container_resultado.visible = False
        self.txt_status.value = "Iniciando procesamiento..."
        await self.page.update_async()
        
        try:
            # Obtener archivos
            archivos_xml = [f for f in os.listdir(self.carpeta_input) 
                           if f.lower().endswith('.xml')]
            total_archivos = len(archivos_xml)
            
            if total_archivos == 0:
                await self.show_error("No se encontraron archivos XML.")
                return

            todos_los_datos = []
            errores = 0
            
            # Procesar cada archivo
            for i, nombre_archivo in enumerate(archivos_xml):
                self.txt_status.value = f"Procesando: {nombre_archivo}\n({i+1} de {total_archivos})"
                self.progress_bar.value = (i + 1) / total_archivos
                await self.page.update_async()
                
                ruta_completa = os.path.join(self.carpeta_input, nombre_archivo)
                
                try:
                    datos_cfdi = await asyncio.to_thread(
                        self.extractor.procesar_cfdi_completo, 
                        ruta_completa
                    )
                    if datos_cfdi:
                        todos_los_datos.append(datos_cfdi)
                    else:
                        errores += 1
                except Exception as ex:
                    print(f"Error procesando {nombre_archivo}: {ex}")
                    errores += 1
                
                await asyncio.sleep(0.01)

            # Generar Excel
            self.progress_bar.value = 1.0
            self.txt_status.value = "Generando archivo Excel..."
            await self.page.update_async()
            
            if not todos_los_datos:
                await self.show_error("No se extrajeron datos válidos de ningún CFDI.")
                return

            nombre_excel = "reporte_cfdi.xlsx"
            ruta_salida_excel = os.path.join(self.carpeta_output, nombre_excel)
            
            if exportar_a_excel is None:
                raise ImportError("No se pudo importar exportar_a_excel. Verifique que pandas y openpyxl estén instalados.")

            await asyncio.to_thread(exportar_a_excel, todos_los_datos, ruta_salida_excel)
            
            # Mostrar éxito
            await self.show_success(len(todos_los_datos), errores, nombre_excel)
            
        except Exception as ex:
            await self.show_error(f"Error inesperado:\n{str(ex)}")
        finally:
            self.btn_procesar.disabled = False
            await self.page.update_async()

    async def show_success(self, procesados, errores, nombre_excel):
        """Muestra mensaje de éxito."""
        self.txt_status.value = "✅ Proceso Finalizado"
        self.progress_bar.visible = False
        
        self.container_resultado.content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "✅ Procesamiento Completado",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color="green"
                    ),
                    ft.Divider(height=20),
                    ft.Text(f"📄 Archivo generado: {nombre_excel}", size=16),
                    ft.Text(f"📊 Archivos procesados: {procesados}", size=16),
                    ft.Text(
                        f"⚠️ Archivos con errores: {errores}", 
                        size=16,
                        color="red" if errores > 0 else "black"
                    ),
                    ft.Divider(height=20),
                    ft.Button(
                        "📂 Abrir carpeta de resultados",
                        on_click=self.open_output_folder,
                        height=45
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
            ),
            padding=30,
            border=ft.border.all(2, "green"),
            border_radius=10
        )
        self.container_resultado.visible = True
        await self.page.update_async()

    async def show_error(self, mensaje):
        """Muestra mensaje de error."""
        self.txt_status.value = "❌ Error"
        self.progress_bar.visible = False
        
        self.container_resultado.content = ft.Container(
            content=ft.Column(
                [
                    ft.Text("❌ Error", size=24, color="red", weight=ft.FontWeight.BOLD),
                    ft.Divider(height=10),
                    ft.Text(mensaje, size=14, color="red")
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
            ),
            padding=30,
            border=ft.border.all(2, "red"),
            border_radius=10
        )
        self.container_resultado.visible = True
        await self.page.update_async()

    def open_output_folder(self, e):
        """Abre carpeta de salida."""
        try:
            if not os.path.exists(self.carpeta_output):
                return
            
            system = platform.system()
            if system == 'Windows':
                os.startfile(self.carpeta_output)
            elif system == 'Darwin':
                subprocess.run(['open', self.carpeta_output])
            else:
                subprocess.run(['xdg-open', self.carpeta_output])
        except Exception as ex:
            print(f"Error al abrir carpeta: {ex}")


def main(page: ft.Page):
    """Punto de entrada."""
    app = CFDIProcessorApp(page)
    page.add(app.build_ui())
    page.update()


if __name__ == "__main__":
    print("🚀 Iniciando Procesador CFDI")
    ft.run(main)