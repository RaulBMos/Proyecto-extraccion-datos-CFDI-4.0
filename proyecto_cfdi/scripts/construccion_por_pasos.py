"""
construccion_por_pasos.py

Ejemplo paso a paso para extraer información básica de un archivo XML CFDI 4.0.
Este módulo muestra cómo obtener atributos del comprobante, datos del emisor,
el UUID del timbre fiscal y la lista de conceptos con sus importes.

Buenas prácticas aplicadas:
- Docstring de módulo explicativo
- Uso de `main()` y guardia `if __name__ == '__main__'` para evitar ejecución al importar
- Comentarios claros antes de bloques lógicos
"""

import xml.etree.ElementTree as ET
import os


def main():
    """Punto de entrada principal que parsea el XML y extrae datos relevantes.

    Se asume que el archivo de ejemplo se llama 'ejemplo_xml_cfdi.xml' y está
    en el directorio de trabajo actual. Ajustar la ruta según sea necesario.
    """

    # Parsear el archivo XML CFDI
    tree = ET.parse('ejemplo_xml_cfdi.xml')
    root = tree.getroot()

    # --- Información del comprobante (atributos del elemento raíz) ---
    # Obtener Serie y Folio: pueden no existir en todos los comprobantes
    serie = root.attrib.get('Serie')
    folio = root.attrib.get('Folio')
    if serie is None or folio is None:
        # Aviso informativo para el usuario si faltan estos atributos
        print("Advertencia: 'Serie' o 'Folio' no encontrado en atributos del comprobante.")
    else:
        print(f"Serie y folio: {serie}-{folio}")

    # Total y fecha de emisión (si están presentes)
    total = root.attrib.get('Total')
    if total is not None:
        print(f"Total: {total}")

    fecha_emision = root.attrib.get('Fecha')
    if fecha_emision is not None:
        print(f"Fecha de emisión: {fecha_emision}")

    # --- Espacios de nombres (namespaces) usados en CFDI 4.0 ---
    namespace = {
        'cfdi': "http://www.sat.gob.mx/cfd/4",
        'tfd': "http://www.sat.gob.mx/TimbreFiscalDigital",
    }

    # --- Emisor: obtener RFC ---
    emisor = root.find('cfdi:Emisor', namespace)
    if emisor is not None:
        rfc = emisor.get('Rfc')
        print(f"RFC del emisor: {rfc}")
    else:
        print("Emisor no encontrado en el XML.")

    # --- Timbre fiscal digital: obtener UUID si existe ---
    timbre = root.find('.//tfd:TimbreFiscalDigital', namespace)
    if timbre is not None:
        uuid = timbre.get('UUID')
        print(f"UUID del timbre fiscal digital: {uuid}")
    else:
        print("Timbre fiscal digital no encontrado.")

    # --- Conceptos: recorrer y mostrar descripción e importe ---
    conceptos = root.findall('cfdi:Conceptos/cfdi:Concepto', namespace)
    print(f"Encontré {len(conceptos)} conceptos:")

    # Usamos enumerate para numerar las líneas (1-based) y facilitar lectura
    for i, concepto in enumerate(conceptos, 1):
        descripcion = concepto.get('Descripcion')
        importe = concepto.get('Importe')
        print(f"  {i}. {descripcion} - ${importe}")


if __name__ == '__main__':
    main()