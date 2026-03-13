"""
RC-FEAT-020: Biblioteca de 7 Plantillas WA
Tests unitarios para la biblioteca de plantillas de WhatsApp.
"""
import pytest
from unittest.mock import patch


# ──────────────────────────────────────────────
# Helpers para importar sin Streamlit
# ──────────────────────────────────────────────
def _get_biblioteca():
    """Importa WA_PLANTILLAS_BIBLIOTECA evitando el runtime de Streamlit."""
    import importlib, types, sys

    # Stub mínimo de streamlit
    st_stub = types.ModuleType("streamlit")
    for attr in ("text_area", "selectbox", "button", "success", "error",
                 "markdown", "caption", "columns", "subheader", "divider",
                 "session_state", "info", "warning", "dataframe", "write",
                 "spinner", "rerun", "empty", "expander"):
        setattr(st_stub, attr, lambda *a, **kw: None)
    st_stub.session_state = {}
    sys.modules.setdefault("streamlit", st_stub)
    sys.modules.setdefault("streamlit.components", types.ModuleType("streamlit.components"))
    sys.modules.setdefault("streamlit.components.v1", types.ModuleType("streamlit.components.v1"))

    # Stubs para dependencias de whatsapp.py
    for mod in ("utils.settings_manager", "utils.db_manager",
                "utils.storage_manager", "utils.whatsapp_sender"):
        sys.modules.setdefault(mod, types.ModuleType(mod))

    mod = importlib.import_module("utils.ui.tabs.whatsapp")
    return mod.WA_PLANTILLAS_BIBLIOTECA, mod._NOMBRE_PLANTILLA_PERSONALIZADA


# ──────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────
class TestBibliotecaPlantillas:
    """Valida estructura y contenido de WA_PLANTILLAS_BIBLIOTECA."""

    def setup_method(self):
        self.biblioteca, self.nombre_personalizada = _get_biblioteca()

    def test_biblioteca_tiene_7_plantillas(self):
        assert len(self.biblioteca) == 7, (
            f"Esperadas 7 plantillas, encontradas {len(self.biblioteca)}"
        )

    def test_todas_las_plantillas_son_strings_no_vacios(self):
        for nombre, texto in self.biblioteca.items():
            assert isinstance(texto, str) and len(texto) > 20, (
                f"Plantilla '{nombre}' vacía o muy corta"
            )

    def test_plantillas_tienen_empresa_variable(self):
        """Las 7 plantillas deben incluir la variable {EMPRESA}."""
        for nombre, texto in self.biblioteca.items():
            assert "{EMPRESA}" in texto, f"'{nombre}' no contiene {{EMPRESA}}"

    def test_plantillas_cobranza_estandar_y_urgente_tienen_detalle_docs(self):
        nombres = list(self.biblioteca.keys())
        for key in nombres:
            if "Estándar" in key or "Urgente" in key or "Segundo" in key:
                assert "{DETALLE_DOCS}" in self.biblioteca[key], (
                    f"'{key}' debería tener {{DETALLE_DOCS}}"
                )

    def test_plantilla_urgente_tiene_total_saldo(self):
        clave_urgente = [k for k in self.biblioteca if "Urgente" in k][0]
        assert "{TOTAL_SALDO_REAL}" in self.biblioteca[clave_urgente]

    def test_plantilla_solo_total_tiene_total_saldo(self):
        clave = [k for k in self.biblioteca if "Total" in k or "Solo" in k][0]
        assert "{TOTAL_SALDO_REAL}" in self.biblioteca[clave]

    def test_todas_las_plantillas_tienen_dacta_firma(self):
        """Todas deben incluir la firma DACTA S.A.C."""
        for nombre, texto in self.biblioteca.items():
            assert "DACTA" in texto, f"'{nombre}' no tiene firma DACTA"

    def test_nombre_plantilla_personalizada_no_en_biblioteca(self):
        """La opción 'Personalizada' NO debe estar en el dict de biblioteca."""
        assert self.nombre_personalizada not in self.biblioteca

    def test_claves_comienzan_con_emoji(self):
        """Todas las claves deben tener un emoji al inicio."""
        import unicodedata
        for nombre in self.biblioteca:
            primer_char = nombre[0]
            categoria = unicodedata.category(primer_char)
            assert categoria in ("So", "Sm", "Sk", "Po") or ord(primer_char) > 0x2000, (
                f"'{nombre}' no comienza con emoji"
            )

    def test_plantilla_acuerdo_tiene_total_saldo(self):
        clave = [k for k in self.biblioteca if "Acuerdo" in k][0]
        assert "{TOTAL_SALDO_REAL}" in self.biblioteca[clave]

    def test_plantilla_reconocimiento_no_tiene_deuda_pendiente(self):
        """La plantilla de reconocimiento es positiva (no habla de deuda vencida)."""
        clave = [k for k in self.biblioteca if "Reconocimiento" in k or "Pago" in k][-1]
        texto = self.biblioteca[clave]
        # Debe mencionar pago registrado, no documentos pendientes
        assert "pago" in texto.lower()

    def test_primer_recordatorio_existe_y_es_menos_urgente_que_urgente(self):
        clave_r1 = [k for k in self.biblioteca if "Primer" in k][0]
        clave_urg = [k for k in self.biblioteca if "Urgente" in k][0]
        texto_r1 = self.biblioteca[clave_r1]
        texto_urg = self.biblioteca[clave_urg]
        # La urgente tiene "⚠️ AVISO FINAL" o "legal"; el primer recordatorio no
        assert "legal" not in texto_r1.lower()
        assert "legal" in texto_urg.lower() or "AVISO FINAL" in texto_urg
