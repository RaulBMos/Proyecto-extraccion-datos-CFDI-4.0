"""
extractor.py

Contiene la clase `CFDIExtractor` responsable de parsear y extraer
información importante de archivos CFDI (XML). El extractor está pensado
para ser tolerante a variantes de namespaces y versiones (3.3/4.0), y para
proveer una estructura de datos consistente que puedan consumir otros
componentes del proyecto (por ejemplo el escritor a Excel).

Buenas prácticas aplicadas:
- Docstrings en módulo y métodos
- Manejo de excepciones controlado
- Comentarios breves en bloques clave para facilitar mantenimiento
"""

import xml.etree.ElementTree as ET
import os
from datetime import datetime


class CFDIExtractor:
    """Extractor para archivos CFDI.

    Métodos principales:
    - `cargar_cfdi`: carga y parsea un archivo XML
    - `procesar_cfdi_completo`: orquesta la extracción y devuelve un dict
    - Varios métodos `extraer_*` devuelven partes concretas del CFDI
    """

    def __init__(self):
        # Namespaces comunes que pueden aparecer en distintos CFDI/Complementos
        self.namespaces = {
            'cfdi': 'http://www.sat.gob.mx/cfd/4',
            'cfdi33': 'http://www.sat.gob.mx/cfd/3',  # Para CFDI 3.3
            'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
            'pago20': 'http://www.sat.gob.mx/Pagos20',
            'pago10': 'http://www.sat.gob.mx/Pagos',  # Versión anterior
            'nomina12': 'http://www.sat.gob.mx/nomina12',
            'cartaporte31': 'http://www.sat.gob.mx/CartaPorte31'
        }

    def cargar_cfdi(self, archivo_path):
        """Carga y parsea un archivo XML.

        Valida que el archivo exista y que el contenido sea un XML válido. En
        caso de error devuelve `None` y muestra un mensaje útil para debug.
        """
        try:
            if not os.path.exists(archivo_path):
                raise FileNotFoundError(f"No se encontró el archivo: {archivo_path}")

            tree = ET.parse(archivo_path)
            root = tree.getroot()

            # Detectar versión para información al usuario
            version = self.detectar_version(root)
            print(f"📄 CFDI Versión {version} cargado correctamente")

            return root

        except ET.ParseError as e:
            # Error al parsear XML: normalmente indica XML mal formado
            print(f"❌ Error al parsear XML: {e}")
            return None
        except Exception as e:
            # Otros errores (permiso, IO, etc.)
            print(f"❌ Error inesperado: {e}")
            return None

    def detectar_version(self, root):
        """Intenta determinar la versión del CFDI.

        Primero inspecciona atributos 'Version'/'version', si no encuentra nada
        intenta inferirla a partir del tag o namespace.
        """
        version = root.get('Version') or root.get('version')
        if version:
            return version

        # Intento heurístico: buscar indicadores en el tag
        tag_lower = (root.tag or '').lower()
        if 'cfd/4' in tag_lower or 'cfdi' in tag_lower and '4' in tag_lower:
            return "4.0"
        elif 'cfd/3' in tag_lower or 'cfdi' in tag_lower and '3' in tag_lower:
            return "3.3"
        else:
            return "Desconocida"

    def extraer_datos_generales(self, root):
        """Extrae atributos generales del comprobante (serie, folio, totales, etc.)."""
        datos = {
            'version': root.get('Version'),
            'serie': root.get('Serie', 'Sin Serie'),
            'folio': root.get('Folio', 'Sin Folio'),
            'fecha': root.get('Fecha'),
            # Usar get con valor por defecto para evitar TypeError en float(None)
            'subtotal': float(root.get('SubTotal', 0)),
            'total': float(root.get('Total', 0)),
            'moneda': root.get('Moneda', 'MXN'),
            'tipo_comprobante': self.traducir_tipo_comprobante(root.get('TipoDeComprobante')),
            'metodo_pago': root.get('MetodoPago', 'Pago parcial'),
            'lugar_expedicion': root.get('LugarExpedicion', 'SIN_LUGAR')
        }
        return datos

    def traducir_tipo_comprobante(self, tipo):
        """Mapea códigos de tipo de comprobante a descripciones legibles."""
        tipos = {
            'I': 'Ingreso (Factura)',
            'E': 'Egreso (Nota de Crédito)',
            'P': 'Pago',
            'N': 'Nómina',
            'T': 'Traslado'
        }
        return tipos.get(tipo, f'Desconocido ({tipo})')

    def extraer_emisor(self, root):
        """Extrae información del emisor intentando en distintos namespaces."""
        emisor = root.find('cfdi:Emisor', self.namespaces)
        if emisor is None:
            # Intentar con la etiqueta usada en CFDI 3.3
            emisor = root.find('cfdi33:Emisor', self.namespaces)

        if emisor is not None:
            return {
                'rfc': emisor.get('Rfc'),
                'nombre': emisor.get('Nombre', 'Sin Nombre'),
                'regimen_fiscal': emisor.get('RegimenFiscal'),
            }
        # Devolver estructura consistente aunque falte el emisor
        return {'rfc': None, 'nombre': None, 'regimen_fiscal': None}

    def extraer_receptor(self, root):
        """Extrae información del receptor (cliente) con fallback entre versiones."""
        receptor = root.find('cfdi:Receptor', self.namespaces)
        if receptor is None:
            receptor = root.find('cfdi33:Receptor', self.namespaces)

        if receptor is not None:
            return {
                'rfc': receptor.get('Rfc'),
                'nombre': receptor.get('Nombre', 'Sin Nombre'),
                'uso_cfdi': receptor.get('UsoCFDI'),
                'regimen_fiscal': receptor.get('RegimenFiscalReceptor'),
                'domicilio_fiscal': receptor.get('DomicilioFiscalReceptor'),
                'domicilio_fiscal_receptor': receptor.get('DomicilioFiscalReceptor')
            }
        return {'rfc': None, 'nombre': None, 'uso_cfdi': None, 'regimen_fiscal': None, 'domicilio_fiscal': None, 'domicilio_fiscal_receptor': None }

    def extraer_conceptos(self, root):
        """Extrae la lista de conceptos y normaliza tipos numéricos.

        Devuelve una lista de diccionarios con información del concepto y sus impuestos.
        """
        conceptos = root.findall('cfdi:Conceptos/cfdi:Concepto', self.namespaces)
        if not conceptos:
            conceptos = root.findall('cfdi33:Conceptos/cfdi33:Concepto', self.namespaces)

        lista_conceptos = []
        for concepto in conceptos:
            concepto_data = {
                'clave_prod_serv': concepto.get('ClaveProdServ'),
                'cantidad': float(concepto.get('Cantidad', 0)),
                'clave_unidad': concepto.get('ClaveUnidad'),
                'descripcion': concepto.get('Descripcion'),
                'valor_unitario': float(concepto.get('ValorUnitario', 0)),
                'importe': float(concepto.get('Importe', 0)),
                'descuento': float(concepto.get('Descuento', 0)),
                'objeto_imp': concepto.get('ObjetoImp')
            }

            # Extraer impuestos asociados al concepto
            concepto_data['impuestos'] = self.extraer_impuestos_concepto(concepto)
            lista_conceptos.append(concepto_data)

        return lista_conceptos

    def extraer_impuestos_concepto(self, concepto):
        """Extrae traslados y retenciones definidos dentro de un concepto."""
        impuestos = {'traslados': [], 'retenciones': []}

        # Buscar elementos de traslado dentro del concepto
        traslados = concepto.findall('.//cfdi:Traslado', self.namespaces)
        for traslado in traslados:
            impuestos['traslados'].append({
                'base': float(traslado.get('Base', 0)),
                'impuesto': traslado.get('Impuesto'),
                'tipo_factor': traslado.get('TipoFactor'),
                'tasa_cuota': float(traslado.get('TasaOCuota', 0)),
                'importe': float(traslado.get('Importe', 0))
            })

        # Buscar retenciones dentro del concepto
        retenciones = concepto.findall('.//cfdi:Retencion', self.namespaces)
        for retencion in retenciones:
            impuestos['retenciones'].append({
                'base': float(retencion.get('Base', 0)),
                'impuesto': retencion.get('Impuesto'),
                'tipo_factor': retencion.get('TipoFactor'),
                'tasa_cuota': float(retencion.get('TasaOCuota', 0)),
                'importe': float(retencion.get('Importe', 0))
            })

        return impuestos

    def extraer_timbre(self, root):
        """Extrae la información del timbre fiscal digital si existe."""
        timbre = root.find('.//tfd:TimbreFiscalDigital', self.namespaces)
        if timbre is not None:
            return {
                'uuid': timbre.get('UUID'),
                'fecha_timbrado': timbre.get('FechaTimbrado'),
                'rfc_prov_certif': timbre.get('RfcProvCertif'),
                'no_certificado_sat': timbre.get('NoCertificadoSAT')
            }
        return {}

    def extraer_complementos(self, root):
        """Detecta y extrae complementos presentes en el CFDI (ej. Pagos)."""
        complementos = {}

        # Complemento de Pagos: soportar tanto pagos v2.0 como v1.0
        pagos = root.find('.//pago20:Pagos', self.namespaces)
        if not pagos:
            pagos = root.find('.//pago10:Pagos', self.namespaces)

        if pagos is not None:
            complementos['pagos'] = self.extraer_complemento_pagos(pagos)

        # Otros complementos (nómina, carta porte, comercio exterior, etc.)
        # pueden añadirse aquí siguiendo la misma estructura.

        return complementos

    def extraer_complemento_pagos(self, pagos):
        """Extrae la lista de pagos y los documentos relacionados por pago."""
        datos_pagos = []

        # Buscar elementos Pago dentro del complemento
        lista_pagos = pagos.findall('.//pago20:Pago', self.namespaces)
        if not lista_pagos:
            lista_pagos = pagos.findall('.//pago10:Pago', self.namespaces)

        for pago in lista_pagos:
            pago_data = {
                'fecha_pago': pago.get('FechaPago'),
                'forma_pago': pago.get('FormaDePagoP'),
                'moneda': pago.get('MonedaP'),
                'monto': float(pago.get('Monto', 0)),
                'documentos_relacionados': []
            }

            # Documentos relacionados con este pago (DoctoRelacionado)
            docs = pago.findall('.//pago20:DoctoRelacionado', self.namespaces)
            if not docs:
                docs = pago.findall('.//pago10:DoctoRelacionado', self.namespaces)

            for doc in docs:
            # Extraer información de impuestos trasladados (TrasladoDR)
                traslados_dr = []
                impuestos_dr = doc.find('.//pago20:ImpuestosDR', self.namespaces)
                if impuestos_dr is None:
                    impuestos_dr = doc.find('.//pago10:ImpuestosDR', self.namespaces)
                
                if impuestos_dr is not None:
                    traslados = impuestos_dr.findall('.//pago20:TrasladoDR', self.namespaces)
                    if not traslados:
                        traslados = impuestos_dr.findall('.//pago10:TrasladoDR', self.namespaces)
                    
                    for traslado in traslados:
                        traslados_dr.append({
                            'base': float(traslado.get('BaseDR', 0)),
                            'impuesto': traslado.get('ImpuestoDR'),
                            'tipo_factor': traslado.get('TipoFactorDR'),
                            'tasa_cuota': float(traslado.get('TasaOCuotaDR', 0)),
                            'importe': float(traslado.get('ImporteDR', 0))
                        })
                
                # Construir el diccionario del documento relacionado
                doc_relacionado = {
                    'id_documento': doc.get('IdDocumento'),
                    'serie': doc.get('Serie'),
                    'folio': doc.get('Folio'),
                    'moneda': doc.get('MonedaDR'),
                    'imp_saldo_ant': float(doc.get('ImpSaldoAnt', 0)),
                    'imp_pagado': float(doc.get('ImpPagado', 0)),
                    'imp_saldo_insoluto': float(doc.get('ImpSaldoInsoluto', 0)),
                    'traslados_dr': traslados_dr
                }
                
                pago_data['documentos_relacionados'].append(doc_relacionado)
            datos_pagos.append(pago_data)

        return datos_pagos

    def procesar_cfdi_completo(self, archivo_path):
        """Orquesta la extracción completa y devuelve un diccionario con resultados."""
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
            'complementos': self.extraer_complementos(root),
            'impuestos': self.extraer_impuestos_concepto(root),
        }

        # Mostrar un resumen amigable en consola
        self.mostrar_resumen(resultado)

        return resultado

    def mostrar_resumen(self, datos):
        """Imprime en consola un breve resumen de los datos extraídos."""
        print(f"📊 RESUMEN DEL CFDI")
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
