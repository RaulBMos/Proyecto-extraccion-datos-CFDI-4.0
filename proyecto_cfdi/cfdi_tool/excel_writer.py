"""
excel_writer.py

Funciones para exportar la información extraída de CFDI a un archivo Excel.

La función principal `exportar_a_excel` espera una lista de diccionarios con la
estructura resultante del extractor y genera un archivo Excel con varias hojas:
- `CFDI_General`: resumen por comprobante
- `Conceptos`: todos los conceptos relacionados a cada comprobante
- `Documentos Relacionados`: si existen (por ejemplo en complementos de pagos)

Requiere `pandas` y `openpyxl` como engine para escritura Excel.
"""

import pandas as pd


def exportar_a_excel(lista_datos_cfdi, ruta_salida):
    """Exporta una lista de datos CFDI a un archivo Excel con hojas separadas.

    Parámetros:
    - lista_datos_cfdi (list): Lista de diccionarios con la información extraída.
    - ruta_salida (str): Ruta (incluido nombre) donde guardar el archivo .xlsx.

    La función crea tres DataFrames intermedios y los escribe en hojas separadas.
    En caso de error durante la escritura, captura la excepción y la muestra.
    """

    print(f"\n--- Iniciando la exportación a Excel ---")
    print(f"Se exportarán datos de {len(lista_datos_cfdi)} CFDI.")

    # Listas intermedias para construir DataFrames
    filas_general = []
    filas_conceptos = []
    filas_documentos_relacionados = []

    # Recorrer cada elemento (CFDI) y desestructurar la información necesaria
    for datos in lista_datos_cfdi:
        # Obtener UUID del timbre si está disponible, si no usar un valor por defecto
        uuid = datos.get('timbre', {}).get('uuid', 'SIN_UUID')
        
        # Obtener el primer concepto si existe (para la descripción en la hoja general)
        conceptos = datos.get('conceptos', [])
        primer_concepto = conceptos[0] if conceptos else {}
        traslados = datos.get('impuestos', {}).get('traslados', [])

        # Construir fila para la hoja general con campos comunes
        fila_gen = {
            'UUID': uuid,
            'Fecha': datos.get('datos_generales', {}).get('fecha'),
            'Tipo Comprobante': datos.get('datos_generales', {}).get('tipo_comprobante'),
            'Metodo de Pago': datos.get('datos_generales', {}).get('metodo_pago'),
            'Serie': datos.get('datos_generales', {}).get('serie'),
            'Folio': datos.get('datos_generales', {}).get('folio'),
            'Subtotal': datos.get('datos_generales', {}).get('subtotal'),
            'tasa_cuota': traslados[0].get('tasa_cuota') if traslados else 'SIN_TASA', 
            'importe': traslados[0].get('importe') if traslados else 'SIN_IMPORTE',
            'Total': datos.get('datos_generales', {}).get('total'),
            'Moneda': datos.get('datos_generales', {}).get('moneda'),
            'Descripcion': primer_concepto.get('descripcion'),
            'Emisor RFC': datos.get('emisor', {}).get('rfc'),
            'Emisor Nombre': datos.get('emisor', {}).get('nombre'),
            'Receptor RFC': datos.get('receptor', {}).get('rfc'),
            'Receptor Nombre': datos.get('receptor', {}).get('nombre'),
            'Uso CFDI': datos.get('receptor', {}).get('uso_cfdi'),
            'RegimenFiscalReceptor': datos.get('receptor', {}).get('regimen_fiscal'),
            'lugar_expedicion': datos.get('datos_generales', {}).get('lugar_expedicion'),
            'receptor_domicilio_fiscal_receptor': datos.get('receptor', {}).get('domicilio_fiscal_receptor'),
        }
        filas_general.append(fila_gen)

        # Agregar una fila por cada concepto del CFDI (relacionada por UUID)
        for concepto in datos.get('conceptos', []):
            fila_con = {
                'UUID_CFDI': uuid,  # para relacionar con la hoja general
                'ClaveProdServ': concepto.get('clave_prod_serv'),
                'Descripcion': concepto.get('descripcion'),
                'Cantidad': concepto.get('cantidad'),
                'ClaveUnidad': concepto.get('clave_unidad'),
                'ValorUnitario': concepto.get('valor_unitario'),
                'Importe': concepto.get('importe'),
                'Descuento': concepto.get('descuento'),
            }
            filas_conceptos.append(fila_con)

        # Si existen complementos (por ejemplo pagos), construir filas para documentos relacionados
        complementos = datos.get('complementos', {})
        if 'pagos' in complementos:
            for pago in complementos['pagos']:
                # El pago puede tener su propio UUID o usar el del CFDI
                uuid_pago = pago.get('uuid', uuid)
                for doc_rel in pago.get('documentos_relacionados', []):
                    # Extraer el primer traslado si existe (puede haber múltiples)
                    traslados = doc_rel.get('traslados_dr', [])
                    primer_traslado = traslados[0] if traslados else {}
                    
                    fila_doc_rel = {
                        'UUID_CFDI': uuid,  # UUID del CFDI principal
                        'UUID_Pago': uuid_pago,  # UUID del pago si aplica
                        'IdDocumento': doc_rel.get('id_documento'),
                        'Serie': doc_rel.get('serie'),
                        'Folio': doc_rel.get('folio'),
                        'MonedaDR': doc_rel.get('moneda'),
                        'ImpSaldoAnt': doc_rel.get('imp_saldo_ant'),
                        'ImpPagado': doc_rel.get('imp_pagado'),
                        'ImpSaldoInsoluto': doc_rel.get('imp_saldo_insoluto'),
                        'BaseDR': primer_traslado.get('base'),
                        #'ImpuestoDR': primer_traslado.get('impuesto'),
                        #'TipoFactorDR': primer_traslado.get('tipo_factor'),
                        'TasaOCuotaDR': primer_traslado.get('tasa_cuota'),
                        'ImporteDR': primer_traslado.get('importe')
                    }
                    filas_documentos_relacionados.append(fila_doc_rel)

    # Si no hay filas generales, no tiene sentido generar el archivo
    if not filas_general:
        print("No hay datos generales para exportar.")
        return

    try:
        # Crear DataFrames a partir de las listas preparadas
        df_general = pd.DataFrame(filas_general)
        df_conceptos = pd.DataFrame(filas_conceptos)
        df_documentos_relacionados = pd.DataFrame(filas_documentos_relacionados)

        # Escribir a Excel. Se usa openpyxl como engine para compatibilidad con .xlsx
        with pd.ExcelWriter(ruta_salida, engine='openpyxl') as writer:
            df_general.to_excel(writer, sheet_name='CFDI_General', index=False)
            df_conceptos.to_excel(writer, sheet_name='Conceptos', index=False)
            # Escribir la hoja de documentos relacionados sólo si tiene datos
            if not df_documentos_relacionados.empty:
                df_documentos_relacionados.to_excel(writer, sheet_name='Documentos Relacionados', index=False)

        print(f"✅ ¡Éxito! Archivo guardado en: {ruta_salida}")

    except Exception as e:
        # Mensaje informativo para facilitar el diagnóstico en caso de fallo
        print(f"❌ Error al escribir el archivo Excel: {e}")
