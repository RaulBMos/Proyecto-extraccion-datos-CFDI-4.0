# Proyecto Extracción Datos CFDI 4.0

Este proyecto es una aplicación en Python diseñada para extraer información detallada de archivos XML de CFDI (Comprobante Fiscal Digital por Internet) y exportarla a una hoja de cálculo de Excel estructurada. Soporta las versiones 3.3 y 4.0 de CFDI.

## Características

*   Extracción automatizada de datos clave de los XML de CFDI (información general, emisor, receptor, conceptos, timbre fiscal, complementos de pago).
*   Soporte para CFDI versiones 3.3 y 4.0.
*   Exportación de los datos extraídos a un archivo Excel con múltiples hojas (datos generales del CFDI y conceptos detallados).
*   Interfaz de línea de comandos fácil de usar.

## Instalación y Configuración

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/RaulBMos/proyectocfdiexcel.git
    cd proyectocfdiexcel
    ```
2.  **Crear un entorno virtual (recomendado):**
    ```bash
    python -m venv .venv
    ```
3.  **Activar el entorno virtual:**
    *   **Windows:**
        ```bash
        .\.venv\Scripts\activate
        ```
    *   **macOS/Linux:**
        ```bash
        source ./.venv/bin/activate
        ```
4.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

## Uso

1.  Coloca tus archivos XML de CFDI en el directorio `input_cfdi/`.
2.  Ejecuta el script principal:
    ```bash
    python main.py
    ```
3.  Los datos extraídos se guardarán como `reporte_cfdi.xlsx` en el directorio `output_excel/`.

## Estructura del Proyecto

*   `main.py`: Script principal para ejecutar el proceso de extracción.
*   `requirements.txt`: Lista las dependencias de Python.
*   `input_cfdi/`: Directorio donde debes colocar tus archivos XML de CFDI.
*   `output_excel/`: Directorio donde se guardará el informe de Excel generado.
*   `cfdi_tool/`: Contiene la lógica central para la extracción de CFDI y la escritura en Excel.
    *   `extractor.py`: Maneja el análisis de XML y la extracción de datos.
    *   `excel_writer.py`: Se encarga de escribir los datos extraídos en Excel.

## Dependencias

*   `pandas`
*   `openpyxl`
