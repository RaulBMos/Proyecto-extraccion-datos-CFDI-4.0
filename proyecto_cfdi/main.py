"""
proyecto_cfdi.main

Script orquestador que recorre una carpeta con archivos CFDI (XML), extrae
la información mediante `CFDIExtractor` y exporta un reporte consolidado a
Excel usando `exportar_a_excel`.

Este archivo debe permanecer ligero: delega la lógica a `cfdi_tool`.
"""

import os
from cfdi_tool.extractor import CFDIExtractor
# `exportar_a_excel` se importa más tarde (opcional) para permitir ejecutar
# el procesamiento aunque la dependencia `pandas` no esté instalada.


# Rutas relativas al script: cambiar si se desea otra estructura de carpetas
CARPETA_INPUT = 'input_cfdi'
CARPETA_OUTPUT = 'output_excel'


def main():
    """Orquesta el flujo completo: leer, procesar y exportar.

    Pasos:
    1. Construir rutas absolutas para entrada/salida basadas en la ubicación del script.
    2. Validar existencia de la carpeta de entrada y crear la de salida si hace falta.
    3. Encontrar archivos .xml y procesarlos con `CFDIExtractor`.
    4. Exportar los resultados a un archivo Excel.
    """

    print("--- Iniciando el proceso de extracción de CFDI ---")

    # Construir rutas absolutas en base a la ubicación de este archivo
    script_dir = os.path.dirname(__file__)
    input_dir = os.path.abspath(os.path.join(script_dir, CARPETA_INPUT))
    output_dir = os.path.abspath(os.path.join(script_dir, CARPETA_OUTPUT))

    # Validar carpeta de entrada
    if not os.path.isdir(input_dir):
        print(f"Error: La carpeta de entrada '{input_dir}' no existe o no es un directorio.")
        return

    # Asegurar que la carpeta de salida exista
    if not os.path.exists(output_dir):
        print(f"La carpeta de salida '{output_dir}' no existe. Creándola...")
        os.makedirs(output_dir)

    # Buscar archivos XML en la carpeta de entrada (case-insensitive)
    archivos_xml = [f for f in os.listdir(input_dir) if f.lower().endswith('.xml')]

    if not archivos_xml:
        print(f"No se encontraron archivos .xml en '{input_dir}'.")
        return

    print(f"Se encontraron {len(archivos_xml)} CFDI para procesar.")

    # Instanciar extractor (la lógica de parseo está encapsulada en cfdi_tool)
    extractor = CFDIExtractor()
    todos_los_datos = []

    # Procesar cada archivo y recopilar los resultados
    for nombre_archivo in archivos_xml:
        ruta_completa = os.path.join(input_dir, nombre_archivo)
        datos_cfdi = extractor.procesar_cfdi_completo(ruta_completa)
        if datos_cfdi:
            todos_los_datos.append(datos_cfdi)

    if not todos_los_datos:
        print("No se pudo extraer información de ningún archivo CFDI.")
        return

    print(f"\n✅ Se procesaron {len(todos_los_datos)} CFDI con éxito.")

    # --- Exportar resultados a Excel ---
    nombre_excel = "reporte_cfdi.xlsx"
    ruta_salida_excel = os.path.join(output_dir, nombre_excel)
    # Intentar importar la función de exportación sólo en este punto para
    # permitir que el procesamiento funcione aunque `pandas` no esté instalado.
    try:
        from cfdi_tool.excel_writer import exportar_a_excel
    except Exception:
        print("⚠️  No se pudo importar la función de exportación a Excel. Se omitirá la escritura del archivo.")
    else:
        exportar_a_excel(todos_los_datos, ruta_salida_excel)


if __name__ == '__main__':
    main()
