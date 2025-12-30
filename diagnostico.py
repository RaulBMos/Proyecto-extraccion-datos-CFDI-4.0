"""
diagnostico.py

Herramienta pequeña para diagnosticar problemas comunes en archivos XML (CFDI).

El script realiza comprobaciones básicas: existencia, tamaño, lectura de las
primeras líneas (con manejo de codificaciones), inspección de los primeros
bytes para detectar la declaración XML y caracteres problemáticos.
"""

import os


def diagnosticar_archivo_xml(archivo_path):
    """Diagnostica problemas comunes en un archivo XML o CFDI.

    Parámetros:
    - archivo_path (str): Ruta al archivo XML a diagnosticar.

    Retorna:
    - bool: True si el diagnóstico no detectó fallos críticos de lectura,
      False si detectó un problema que impide procesar el archivo.
    """

    print(f"🔍 DIAGNÓSTICO DE: {archivo_path}")
    print("=" * 50)

    # 1) Verificar existencia del archivo
    if not os.path.exists(archivo_path):
        print(f"❌ ERROR: El archivo '{archivo_path}' no existe")
        print("💡 SOLUCIONES:")
        print("   - Verifica que el nombre del archivo sea correcto")
        print("   - Verifica que esté en la carpeta correcta")
        print("   - Usa la ruta completa del archivo")
        return False

    # 2) Verificar tamaño (evitar procesar archivos vacíos)
    tamaño = os.path.getsize(archivo_path)
    print(f"📏 Tamaño del archivo: {tamaño:,} bytes")

    if tamaño == 0:
        print("❌ ERROR: El archivo está vacío")
        return False

    # 3) Mostrar las primeras líneas para inspección visual
    print("\n📖 PRIMERAS 10 LÍNEAS DEL ARCHIVO:")
    print("-" * 40)

    # Intentar leer con UTF-8 y, en caso de error, reintentar con Latin-1
    try:
        with open(archivo_path, 'r', encoding='utf-8') as file:
            for i, linea in enumerate(file, 1):
                if i <= 10:
                    # Usamos repr() para hacer visibles caracteres especiales
                    linea_limpia = repr(linea.rstrip())
                    print(f"{i:2}: {linea_limpia}")
                else:
                    break
    except UnicodeDecodeError:
        print("⚠️  Problema de codificación UTF-8, intentando con Latin-1...")
        try:
            with open(archivo_path, 'r', encoding='latin-1') as file:
                for i, linea in enumerate(file, 1):
                    if i <= 10:
                        linea_limpia = repr(linea.rstrip())
                        print(f"{i:2}: {linea_limpia}")
                    else:
                        break
        except Exception as e:
            # Si aún no se puede leer, mostrar error y abortar diagnóstico
            print(f"❌ No se puede leer el archivo: {e}")
            return False

    # 4) Revisar los primeros bytes para detectar declaración XML y posibles binarios
    print("\n🔍 ANÁLISIS:")
    with open(archivo_path, 'rb') as file:
        primeros_bytes = file.read(100)

    # Mostrar un resumen hex y texto (ignorando errores de decodificación)
    print(f"Primeros bytes (hex): {primeros_bytes[:20].hex()}")
    print(f"Primeros caracteres: {repr(primeros_bytes[:50].decode('utf-8', errors='ignore'))}")

    # 5) Verificaciones específicas: declaración XML y formato
    contenido_inicio = primeros_bytes.decode('utf-8', errors='ignore')

    if not contenido_inicio.strip().startswith('<?xml'):
        print("❌ ERROR: El archivo no comienza con '<?xml'")
        print("💡 Este podría ser el problema principal")

        if contenido_inicio.startswith('<'):
            # Posible XML válido pero sin declaración de encabezado
            print("   - El archivo parece ser XML pero sin declaración")
            print("   - Intenta agregar '<?xml version=\"1.0\" encoding=\"UTF-8\"?>' al inicio")
        else:
            # No parece ser XML
            print("   - El archivo no parece ser XML")
            print("   - Verifica que sea realmente un CFDI XML")
    else:
        print("✅ El archivo comienza correctamente con <?xml")

    # 6) Buscar caracteres nulos u otros indicadores de archivo binario/corrupto
    if b'\x00' in primeros_bytes:
        print("❌ ERROR: El archivo contiene caracteres nulos (archivos binarios)")
        print("💡 Este archivo podría estar corrupto o no ser texto")

    # Si hemos llegado hasta aquí, no hay errores críticos de lectura
    return True

def crear_xml_ejemplo_simple():
    """Crea un XML de ejemplo simple para pruebas"""
    xml_ejemplo = '''<?xml version="1.0" encoding="UTF-8"?>
<cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/4" Version="4.0">
    <cfdi:Emisor Rfc="TEST010101001" Nombre="Empresa de Prueba"/>
    <cfdi:Receptor Rfc="XAXX010101000" Nombre="Cliente de Prueba"/>
</cfdi:Comprobante>'''
    
    with open('xml_prueba_simple.xml', 'w', encoding='utf-8') as f:
        f.write(xml_ejemplo)
    
    print("✅ Creado 'xml_prueba_simple.xml' para pruebas")

if __name__ == "__main__":
    # Cambiar aquí el nombre de tu archivo problemático
    # Ajusta la ruta/nombre según tu entorno; por defecto se prueba 'ejemplo_cfdi.xml'
    archivo_a_diagnosticar = 'ejemplo_cfdi.xml'  # 👈 CAMBIA ESTO
    
    print("🏥 DIAGNÓSTICO XML - Detector de Problemas")
    print("=" * 50)
    
    # Listar archivos XML en la carpeta actual
    archivos_xml = [f for f in os.listdir('.') if f.lower().endswith('.xml')]
    
    if archivos_xml:
        print("📁 Archivos XML encontrados en esta carpeta:")
        for archivo in archivos_xml:
            tamaño = os.path.getsize(archivo)
            print(f"   - {archivo} ({tamaño:,} bytes)")
        print()
    else:
        print("⚠️  No se encontraron archivos XML en esta carpeta")
        print()
    
    # Diagnosticar el archivo especificado
    if os.path.exists(archivo_a_diagnosticar):
        diagnosticar_archivo_xml(archivo_a_diagnosticar)
    else:
        print(f"❌ No se encontró '{archivo_a_diagnosticar}'")
        
        # Ofrecer diagnóstico de cualquier XML que encuentre
        if archivos_xml:
            print(f"\n¿Quieres que diagnostique '{archivos_xml[0]}'? (s/n)")
            # En un script real podrías pedir input del usuario
            
    print("\n" + "=" * 50)
    print("💡 SOLUCIONES COMUNES:")
    print("1. Verifica que el archivo sea realmente un CFDI XML")
    print("2. Abre el archivo en un editor de texto para ver su contenido")
    print("3. Si está vacío o corrupto, descárgalo de nuevo")
    print("4. Verifica la codificación del archivo (debe ser UTF-8)")
    print("5. Si el problema persiste, comparte las primeras líneas del archivo")