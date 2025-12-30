import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path so `proyecto_cfdi` can be imported when running tests
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import importlib.util
from pathlib import Path

# Import module by path to avoid package import issues in test env
mod_path = Path(__file__).resolve().parents[1] / 'cfdi_tool' / 'excel_writer.py'
spec = importlib.util.spec_from_file_location('excel_writer_mod', str(mod_path))
excel_writer_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(excel_writer_mod)
exportar_a_excel = excel_writer_mod.exportar_a_excel


def test_exportar_a_excel_crea_archivo(tmp_path):
    # Preparar datos de prueba mínimos
    datos = [
        {
            'archivo': 'test.xml',
            'datos_generales': {'fecha': '2025-12-30T12:00:00', 'tipo_comprobante': 'Ingreso (Factura)', 'serie': 'A', 'folio': '1', 'subtotal': 100.0, 'total': 116.0, 'moneda': 'MXN'},
            'emisor': {'rfc': 'DEMO010101001', 'nombre': 'Empresa Demostrativa'},
            'receptor': {'rfc': 'XAXX010101000', 'nombre': 'Cliente Demo'},
            'conceptos': [
                {'clave_prod_serv': '01010101', 'cantidad': 1.0, 'clave_unidad': 'H87', 'descripcion': 'Servicio', 'valor_unitario': 100.0, 'importe': 100.0, 'descuento': 0}
            ],
            'timbre': {'uuid': 'TEST-UUID-1234'},
            'complementos': {}
        }
    ]

    salida = tmp_path / 'reporte_test.xlsx'
    ruta = str(salida)

    # Ejecutar export
    exportar_a_excel(datos, ruta)

    # Verificar que el archivo fue creado
    assert salida.exists()
