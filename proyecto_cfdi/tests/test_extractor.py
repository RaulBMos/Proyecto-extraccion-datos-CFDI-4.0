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
mod_path = Path(__file__).resolve().parents[1] / 'cfdi_tool' / 'extractor.py'
spec = importlib.util.spec_from_file_location('extractor_mod', str(mod_path))
extractor_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extractor_mod)
CFDIExtractor = extractor_mod.CFDIExtractor


def minimal_cfdi_xml(tmp_path):
    # A minimal CFDI 4.0-like structure for testing extractor parsing
    content = '''<?xml version="1.0" encoding="UTF-8"?>
<cfdi:Comprobante Version="4.0" Serie="A" Folio="1" Fecha="2025-12-30T12:00:00" SubTotal="100" Total="1160" Moneda="MXN" TipoDeComprobante="I" xmlns:cfdi="http://www.sat.gob.mx/cfd/4">
  <cfdi:Emisor Rfc="DEMO010101001" Nombre="Empresa Demostrativa SA de CV" RegimenFiscal="601" />
  <cfdi:Receptor Rfc="XAXX010101000" Nombre="Juan Pérez González" UsoCFDI="G03" />
  <cfdi:Conceptos>
    <cfdi:Concepto ClaveProdServ="01010101" Cantidad="1" ClaveUnidad="H87" Descripcion="Servicio" ValorUnitario="100" Importe="100"/>
  </cfdi:Conceptos>
</cfdi:Comprobante>
'''
    path = tmp_path / "minimal_cfdi.xml"
    path.write_text(content, encoding='utf-8')
    return str(path)


def test_procesar_cfdi_completo(tmp_path):
    extractor = CFDIExtractor()
    archivo = minimal_cfdi_xml(tmp_path)

    resultado = extractor.procesar_cfdi_completo(archivo)

    assert resultado is not None
    assert resultado['archivo'] == archivo
    assert resultado['datos_generales']['serie'] == 'A'
    assert resultado['datos_generales']['folio'] == '1'
    assert resultado['emisor']['rfc'] == 'DEMO010101001'
    assert resultado['receptor']['rfc'] == 'XAXX010101000'
    assert len(resultado['conceptos']) == 1
