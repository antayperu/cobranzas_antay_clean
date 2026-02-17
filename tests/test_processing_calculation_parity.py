import pandas as pd
import pytest

from utils.processing import process_data


def _build_base_inputs(moneda: str, tipcam: float, saldo: float, mondoc: float):
    df_ctas = pd.DataFrame(
        [
            {
                "codcli": 1,
                "nomcli": "Cliente Demo",
                "coddoc": "FT",
                "sersun": "F001",
                "numsun": "00000001",
                "fecdoc": "2026-01-10",
                "fecvct": "2026-01-20",
                "codmnd": moneda,
                "tipcam": tipcam,
                "mododo": saldo,
                "sldacl": saldo,
                "mondoc": mondoc,
                "tipped": "VENTA",
            }
        ]
    )

    df_cartera = pd.DataFrame(
        [
            {
                "codigo_cliente": 1,
                "telefono": "999999999",
                "email": "cliente.demo@antay.com",
                "NOTA": "",
                "Enviar Email": "SI",
            }
        ]
    )

    # Sin movimientos de cobranza: detraccion por regla de negocio (>700 => 12%).
    df_cobranza = pd.DataFrame(columns=["forpag", "coddoc", "numsun", "monpag", "mondoc", "fecpro"])
    return df_ctas, df_cartera, df_cobranza


def test_saldo_real_soles_pending_detraction():
    df_ctas, df_cartera, df_cobranza = _build_base_inputs(
        moneda="SOLES",
        tipcam=3.8,
        saldo=1200.0,
        mondoc=1000.0,
    )

    df_final = process_data(df_ctas, df_cartera, df_cobranza)
    row = df_final.iloc[0]

    assert row["DETRACCIÓN"] == pytest.approx(120.0, rel=0, abs=1e-6)
    assert row["ESTADO DETRACCION"] == "Pendiente"
    assert row["SALDO REAL"] == pytest.approx(1080.0, rel=0, abs=1e-6)


def test_saldo_real_usd_pending_detraction_converted_by_fx():
    df_ctas, df_cartera, df_cobranza = _build_base_inputs(
        moneda="US$",
        tipcam=4.0,
        saldo=1000.0,
        mondoc=1000.0,
    )

    df_final = process_data(df_ctas, df_cartera, df_cobranza)
    row = df_final.iloc[0]

    # 12% de 1000 soles = 120; en USD se resta 120/4 = 30.
    assert row["DETRACCIÓN"] == pytest.approx(120.0, rel=0, abs=1e-6)
    assert row["ESTADO DETRACCION"] == "Pendiente"
    assert row["SALDO REAL"] == pytest.approx(970.0, rel=0, abs=1e-6)


def test_dt_applied_from_cobranza_overrides_detraction_and_preserves_saldo_real():
    df_ctas, df_cartera, _ = _build_base_inputs(
        moneda="SOLES",
        tipcam=3.8,
        saldo=900.0,
        mondoc=1000.0,
    )
    df_cobranza = pd.DataFrame(
        [
            {
                "forpag": "DT",
                # En esta implementacion, el cruce usa:
                # Ctas: coddoc + sersun + numsun
                # Cobranza: coddoc + numsun
                # Para matchear, coddoc en cobranza debe incluir la serie.
                "coddoc": "FTF001",
                "numsun": "00000001",
                "monpag": 200.0,
                "mondoc": 200.0,
                "fecpro": "2026-01-15",
                "nombco": "BCP",
                "codbco": "002",
                "nudopa": "OP-1",
            }
        ]
    )

    df_final = process_data(df_ctas, df_cartera, df_cobranza)
    row = df_final.iloc[0]

    assert row["DETRACCIÓN"] == pytest.approx(200.0, rel=0, abs=1e-6)
    # Ya existe aplicacion DT en cobranza, no debe quedar Pendiente.
    assert row["ESTADO DETRACCION"] != "Pendiente"
    # Si no esta pendiente, saldo real se mantiene igual al saldo.
    assert row["SALDO REAL"] == pytest.approx(row["SALDO"], rel=0, abs=1e-6)
