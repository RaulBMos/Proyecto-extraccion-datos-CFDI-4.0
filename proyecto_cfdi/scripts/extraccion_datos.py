"""
extraccion_datos.py

Script de ejemplo para extraer información básica de un CFDI (XML) usando
xml.etree.ElementTree. El objetivo es mostrar cómo navegar el árbol XML,
usar namespaces y obtener atributos relevantes (serie, folio, emisor, conceptos,
UUID del timbre, complementos de pago, etc.).

Buenas prácticas aplicadas:
- Docstring de módulo
- Comentarios antes de bloques lógicos
- Manejo explícito de excepciones comunes
"""

import xml.etree.ElementTree as ET

# Namespaces necesarios para buscar elementos en un CFDI 4.0
namespaces = {
    'cfdi': 'http://www.sat.gob.mx/cfd/4',
    'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
    'pago20': 'http://www.sat.gob.mx/Pagos20'
}


# Intentar cargar y procesar el XML de ejemplo
try:
    tree = ET.parse('ejemplo_xml_cfdi.xml')
    root = tree.getroot()
    print("✅ Archivo cargado correctamente")

    # Información general del documento
    print(f"Elemento raíz: {root.tag}")
    print(f"Total de atributos en raíz: {len(root.attrib)}")

    # --- DATOS GENERALES DEL COMPROBANTE ---
    # Usar .get() para evitar KeyError si el atributo no existe
    print("\n--- DATOS GENERALES ---")
    print(f"Serie: {root.get('Serie')}")
    print(f"Folio: {root.get('Folio')}")
    print(f"Fecha: {root.get('Fecha')}")
    print(f"Total: ${root.get('Total')}")
    print(f"Tipo: {root.get('TipoDeComprobante')}")

    # --- DATOS DEL EMISOR ---
    # Buscar el elemento Emisor dentro del namespace 'cfdi'
    print("\n--- EMISOR ---")
    emisor = root.find('cfdi:Emisor', namespaces)
    if emisor is not None:
        print(f"RFC: {emisor.get('Rfc')}")
        print(f"Nombre: {emisor.get('Nombre')}")
        print(f"Régimen: {emisor.get('RegimenFiscal')}")

    # --- DATOS DEL RECEPTOR ---
    print("\n--- RECEPTOR ---")
    receptor = root.find('cfdi:Receptor', namespaces)
    if receptor is not None:
        print(f"RFC: {receptor.get('Rfc')}")
        print(f"Nombre: {receptor.get('Nombre')}")
        print(f"Uso CFDI: {receptor.get('UsoCFDI')}")

    # --- CONCEPTOS ---
    # Obtener todos los conceptos y recorrerlos de forma numerada
    conceptos = root.findall('cfdi:Conceptos/cfdi:Concepto', namespaces)
    print(f"\n--- CONCEPTOS ({len(conceptos)} encontrados) ---")

    for i, concepto in enumerate(conceptos, 1):
        print(f"Concepto {i}:")
        print(f"  - Descripción: {concepto.get('Descripcion')}")
        print(f"  - Cantidad: {concepto.get('Cantidad')}")
        print(f"  - Valor Unitario: ${concepto.get('ValorUnitario')}")
        print(f"  - Importe: ${concepto.get('Importe')}")

    # --- TIMBRE FISCAL DIGITAL ---
    # El timbre puede encontrarse en un namespace diferente (tfd)
    print("\n--- TIMBRE FISCAL ---")
    timbre = root.find('.//tfd:TimbreFiscalDigital', namespaces)
    if timbre is not None:
        print(f"UUID: {timbre.get('UUID')}")
        print(f"Fecha Timbrado: {timbre.get('FechaTimbrado')}")

    # --- COMPLEMENTO DE PAGO (PAGOS 2.0) ---
    pago = root.find('.//pago20:Pagos', namespaces)
    if pago is not None:
        print(f"\n--- COMPLEMENTO DE PAGO ---")
        print("✅ Este CFDI incluye información de pago")
        pago_detalle = root.find('.//pago20:Pago', namespaces)
        if pago_detalle is not None:
            print(f"Monto del pago: ${pago_detalle.get('Monto')}")
            print(f"Fecha del pago: {pago_detalle.get('FechaPago')}")
    else:
        print("\n❌ No incluye complemento de pago")

except FileNotFoundError:
    # Mensaje claro para el usuario cuando el archivo no está presente
    print("❌ Error: No se encontró el archivo 'ejemplo_cfdi.xml'")
    print("   Asegúrate de que el archivo esté en la misma carpeta que este script")
except ET.ParseError as e:
    # Error de análisis XML: mostrar el mensaje del parser
    print(f"❌ Error al parsear XML: {e}")
except Exception as e:
    # Captura cualquier otra excepción inesperada para diagnóstico
    print(f"❌ Error inesperado: {e}")

print("\n🎉 Script completado")