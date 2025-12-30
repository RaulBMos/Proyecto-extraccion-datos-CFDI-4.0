"""
cfdi_extractor.py

Clase y utilidades para cargar y extraer datos de archivos CFDI (XML).

Este archivo contiene un extractor simple y tolerante a variantes de
namespaces y versiones (CFDI 3.3/4.0). Los métodos devuelven estructuras
consistentes (diccionarios y listas) para consumo por otras partes del
proyecto (por ejemplo, exportación a Excel).
"""

import xml.etree.ElementTree as ET
import os
from datetime import datetime


class CFDIExtractor:
    """Extractor para archivos CFDI.

    Notas:
    - Intenta manejar distintas versiones y namespaces.
    - Todos los métodos devuelven estructuras consistentes aunque falten
      algunos atributos en el XML (evita lanzar excepciones inesperadas).
    """

    def __init__(self):
        # Namespaces habituales que puede contener un CFDI o sus complementos
        self.namespaces = {
            'cfdi': 'http://www.sat.gob.mx/cfd/4',
            'cfdi33': 'http://www.sat.gob.mx/cfd/3',  # Compatibilidad con 3.3
            'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
            'pago20': 'http://www.sat.gob.mx/Pagos20',
            'pago10': 'http://www.sat.gob.mx/Pagos',  # Versión antigua de pagos
            'nomina12': 'http://www.sat.gob.mx/nomina12',
            'cartaporte31': 'http://www.sat.gob.mx/CartaPorte31'
        }

    def cargar_cfdi(self, archivo_path):
        """Carga un archivo XML y retorna el elemento raíz (or None).

        Validaciones realizadas:
        - existencia del archivo
        - parseo válido del XML
        """
        try:
            if not os.path.exists(archivo_path):
                raise FileNotFoundError(f"No se encontró el archivo: {archivo_path}")

            tree = ET.parse(archivo_path)
            root = tree.getroot()

            version = self.detectar_version(root)
            print(f"📄 CFDI Versión {version} cargado correctamente")

            return root

        except ET.ParseError as e:
            print(f"❌ Error al parsear XML: {e}")
            return None
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return None

    def detectar_version(self, root):
        """Detecta la versión del CFDI intentando varias heurísticas.

        Prioridad:
        1) Atributo 'Version' o 'version'
        2) Inferencia desde el tag/namespace
        """
        version = root.get('Version') or root.get('version')
        if version:
            return version

        tag_lower = (root.tag or '').lower()
        if 'cfd/4' in tag_lower:
            return '4.0'
        if 'cfd/3' in tag_lower:
            return '3.3'
        return 'Desconocida'

    def extraer_datos_generales(self, root):
        """Extrae atributos generales del comprobante (serie, folio, totales...)."""
        # Se usan valores por defecto para evitar errores si faltan atributos
        datos = {
            'version': root.get('Version'),
            'serie': root.get('Serie', 'Sin Serie'),
            'folio': root.get('Folio', 'Sin Folio'),
            'fecha': root.get('Fecha'),
            'subtotal': float(root.get('SubTotal', 0)),
            'total': float(root.get('Total', 0)),
            'moneda': root.get('Moneda', 'MXN'),
            'tipo_comprobante': self.traducir_tipo_comprobante(root.get('TipoDeComprobante')),
            'metodo_pago': root.get('MetodoPago', 'No especificado'),
            'lugar_expedicion': root.get('LugarExpedicion')
        }
        return datos

    def traducir_tipo_comprobante(self, tipo):
        """Convierte el código del tipo de comprobante a una descripción legible."""
        tipos = {
            'I': 'Ingreso (Factura)',
            'E': 'Egreso (Nota de Crédito)',
            'P': 'Pago',
            'N': 'Nómina',
            'T': 'Traslado'
        }
        return tipos.get(tipo, f'Desconocido ({tipo})')

    def extraer_emisor(self, root):
        """Localiza el elemento Emisor en distintos namespaces y devuelve datos."""
        emisor = root.find('cfdi:Emisor', self.namespaces)
        if emisor is None:
            emisor = root.find('cfdi33:Emisor', self.namespaces)

        if emisor is None:
            return {'rfc': None, 'nombre': None, 'regimen_fiscal': None}

        return {
            'rfc': emisor.get('Rfc'),
            'nombre': emisor.get('Nombre', 'Sin Nombre'),
            'regimen_fiscal': emisor.get('RegimenFiscal')
        }

    def extraer_receptor(self, root):
        """Extrae información del receptor (cliente) con fallbacks de versión."""
        receptor = root.find('cfdi:Receptor', self.namespaces)
        if receptor is None:
            receptor = root.find('cfdi33:Receptor', self.namespaces)

        if receptor is None:
            return {}

        return {
            'rfc': receptor.get('Rfc'),
            'nombre': receptor.get('Nombre', 'Sin Nombre'),
            'uso_cfdi': receptor.get('UsoCFDI'),
            'regimen_fiscal': receptor.get('RegimenFiscalReceptor'),
            'domicilio_fiscal': receptor.get('DomicilioFiscalReceptor')
        }

    def extraer_conceptos(self, root):
        """Recupera todos los conceptos y normaliza tipos numéricos."""
        conceptos = root.findall('cfdi:Conceptos/cfdi:Concepto', self.namespaces)
        if not conceptos:
            conceptos = root.findall('cfdi33:Conceptos/cfdi33:Concepto', self.namespaces)

        lista = []
        for concepto in conceptos:
            c = {
                'clave_prod_serv': concepto.get('ClaveProdServ'),
                'cantidad': float(concepto.get('Cantidad', 0)),
                'clave_unidad': concepto.get('ClaveUnidad'),
                'descripcion': concepto.get('Descripcion'),
                'valor_unitario': float(concepto.get('ValorUnitario', 0)),
                'importe': float(concepto.get('Importe', 0)),
                'descuento': float(concepto.get('Descuento', 0)),
                'objeto_imp': concepto.get('ObjetoImp')
            }
            c['impuestos'] = self.extraer_impuestos_concepto(concepto)
            lista.append(c)

        return lista

    def extraer_impuestos_concepto(self, concepto):
        """Extrae traslados y retenciones dentro de un elemento Concepto."""
        impuestos = {'traslados': [], 'retenciones': []}

        traslados = concepto.findall('.//cfdi:Traslado', self.namespaces)
        for t in traslados:
            impuestos['traslados'].append({
                'base': float(t.get('Base', 0)),
                'impuesto': t.get('Impuesto'),
                'tipo_factor': t.get('TipoFactor'),
                'tasa_cuota': float(t.get('TasaOCuota', 0)),
                'importe': float(t.get('Importe', 0))
            })

        retenciones = concepto.findall('.//cfdi:Retencion', self.namespaces)
        for r in retenciones:
            impuestos['retenciones'].append({
                'base': float(r.get('Base', 0)),
                'impuesto': r.get('Impuesto'),
                'tipo_factor': r.get('TipoFactor'),
                'tasa_cuota': float(r.get('TasaOCuota', 0)),
                'importe': float(r.get('Importe', 0))
            })

        return impuestos

    def extraer_timbre(self, root):
        """Extrae datos del Timbrado Fiscal Digital si está presente."""
        timbre = root.find('.//tfd:TimbreFiscalDigital', self.namespaces)
        if timbre is None:
            return {}

        return {
            'uuid': timbre.get('UUID'),
            'fecha_timbrado': timbre.get('FechaTimbrado'),
            'rfc_prov_certif': timbre.get('RfcProvCertif'),
            'no_certificado_sat': timbre.get('NoCertificadoSAT')
        }

    def extraer_complementos(self, root):
        """Detecta y extrae complementos (p.ej. pagos) presentes en el CFDI."""
        complementos = {}

        pagos = root.find('.//pago20:Pagos', self.namespaces)
        if pagos is None:
            pagos = root.find('.//pago10:Pagos', self.namespaces)

        if pagos is not None:
            complementos['pagos'] = self.extraer_complemento_pagos(pagos)

        # Se pueden añadir más complementos aquí (nómina, carta porte, etc.)
        return complementos

    def extraer_complemento_pagos(self, pagos):
        """Extrae la estructura de Pagos y sus documentos relacionados."""
        lista_pagos = pagos.findall('.//pago20:Pago', self.namespaces)
        if not lista_pagos:
            lista_pagos = pagos.findall('.//pago10:Pago', self.namespaces)

        resultados = []
        for pago in lista_pagos:
            pago_data = {
                'fecha_pago': pago.get('FechaPago'),
                'forma_pago': pago.get('FormaDePagoP'),
                'moneda': pago.get('MonedaP'),
                'monto': float(pago.get('Monto', 0)),
                'documentos_relacionados': []
            }

            docs = pago.findall('.//pago20:DoctoRelacionado', self.namespaces)
            if not docs:
                docs = pago.findall('.//pago10:DoctoRelacionado', self.namespaces)

            for doc in docs:
                pago_data['documentos_relacionados'].append({
                    'id_documento': doc.get('IdDocumento'),
                    'serie': doc.get('Serie'),
                    'folio': doc.get('Folio'),
                    'moneda': doc.get('MonedaDR'),
                    'imp_saldo_ant': float(doc.get('ImpSaldoAnt', 0)),
                    'imp_pagado': float(doc.get('ImpPagado', 0)),
                    'imp_saldo_insoluto': float(doc.get('ImpSaldoInsoluto', 0))
                })

            resultados.append(pago_data)

        return resultados

    def procesar_cfdi_completo(self, archivo_path):
        """Orquesta la extracción completa y devuelve un diccionario con los datos."""
        print(f"🔍 Procesando: {archivo_path}")
        print("=" * 50)

        root = self.cargar_cfdi(archivo_path)
        if root is None:
            return None

        resultado = {
            'archivo': archivo_path,
            'fecha_procesamiento': datetime.now().isoformat(),
            'datos_generales': self.extraer_datos_generales(root),
            'emisor': self.extraer_emisor(root),
            'receptor': self.extraer_receptor(root),
            'conceptos': self.extraer_conceptos(root),
            'timbre': self.extraer_timbre(root),
            'complementos': self.extraer_complementos(root)
        }

        # Resumen para el operador
        self.mostrar_resumen(resultado)
        return resultado

    def mostrar_resumen(self, datos):
        """Imprime un resumen compacto y legible de la extracción."""
        print("📊 RESUMEN DEL CFDI")
        print(f"UUID: {datos['timbre'].get('uuid', 'No disponible')}")
        print(f"Tipo: {datos['datos_generales']['tipo_comprobante']}")
        print(f"Serie-Folio: {datos['datos_generales']['serie']}-{datos['datos_generales']['folio']}")
        print(f"Total: ${datos['datos_generales']['total']:,.2f} {datos['datos_generales']['moneda']}")
        print(f"Emisor: {datos['emisor']['nombre']} ({datos['emisor']['rfc']})")
        print(f"Receptor: {datos['receptor'].get('nombre', 'Sin nombre')} ({datos['receptor'].get('rfc')})")
        print(f"Conceptos: {len(datos['conceptos'])} artículos/servicios")
        if datos['complementos']:
            print(f"Complementos: {', '.join(datos['complementos'].keys())}")
        print("✅ Procesamiento completado\n")


# Ejemplo de uso local (se ejecuta sólo si el archivo se corre directamente)
if __name__ == '__main__':
    extractor = CFDIExtractor()
    resultado = extractor.procesar_cfdi_completo('1a3e0f9a-ec50-4020-bf93-33f613599acb.xml')
    if resultado:
        print('🎉 Extracción de ejemplo completada')