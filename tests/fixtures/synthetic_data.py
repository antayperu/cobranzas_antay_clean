"""
Synthetic Data Fixtures for Automated Testing
Genera datos sintéticos para tests sin depender de archivos Excel reales.
"""

import pandas as pd
from datetime import datetime, timedelta

def create_synthetic_df_final(num_records=10, with_emails=True, with_duplicates=False):
    """
    Crea un DataFrame sintético que simula df_final (SSOT).
    
    Args:
        num_records: Número de registros a generar
        with_emails: Si True, incluye emails válidos
        with_duplicates: Si True, algunos clientes comparten el mismo email
    
    Returns:
        pd.DataFrame con estructura similar a df_final
    """
    data = []
    
    for i in range(num_records):
        # Email duplicado para algunos registros si with_duplicates=True
        if with_duplicates and i % 3 == 0:
            email = "shared@example.com"
        elif with_emails:
            email = f"cliente{i}@example.com"
        else:
            email = ""
        
        # Variar saldos y detracciones
        saldo_real = 1000.0 * (i + 1) if i % 5 != 0 else 0.0  # Cada 5to registro tiene saldo 0
        detraccion = 100.0 if i % 7 == 0 else 0.0  # Cada 7mo registro tiene detracción
        estado_detraccion = "PENDIENTE" if detraccion > 0 else "APLICADA"
        
        record = {
            'COD CLIENTE': f'CLI{i:03d}',
            'EMPRESA': f'Empresa {i}',
            'EMAIL_FINAL': email,
            'CORREO': email,  # Columna legacy
            'TELÉFONO': f'99999{i:04d}',
            'SALDO REAL': saldo_real,
            'DETRACCIÓN': detraccion,
            'ESTADO DETRACCION': estado_detraccion,
            'MONEDA': 'SOLES' if i % 2 == 0 else 'DOLARES',
            'COMPROBANTE': f'FAC-{i:04d}',
            'FECH EMIS': (datetime.now() - timedelta(days=30+i)).strftime('%Y-%m-%d'),
            'FECH VENC': (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
            'DÍAS MORA': i,
            'ESTADO DEUDA': 'Gestión Pre-Legal' if i % 3 == 0 else 'Gestión Administrativa',
            'TIPO PEDIDO': 'VENTA',
            'MONT EMIT': saldo_real + detraccion,
            'SALDO': saldo_real,
            'AMORTIZACIONES': 0.0,
            'TIPO CAMBIO': 3.75,
            'NOTA': '',
            'MATCH_KEY': f'CLI{i:03d}_FAC-{i:04d}',
            # Tracking columns (inicializadas como PENDIENTE)
            'ESTADO_EMAIL': 'PENDIENTE',
            'FECHA_ULTIMO_ENVIO': '',
        }
        data.append(record)
    
    # Calcular DETR_PENDIENTE_AMOUNT
    df = pd.DataFrame(data)
    df['DETR_PENDIENTE_AMOUNT'] = df.apply(
        lambda x: float(x['DETRACCIÓN']) if x['ESTADO DETRACCION'] == 'PENDIENTE' else 0.0,
        axis=1
    )
    
    return df


def create_synthetic_df_filtered(df_final, filter_empresa=None, filter_moneda=None, only_with_email=False):
    """
    Crea un DataFrame filtrado a partir de df_final (simula filtros del Reporte General).
    
    Args:
        df_final: DataFrame base (SSOT)
        filter_empresa: Nombre de empresa para filtrar (ej: "Empresa 1")
        filter_moneda: Moneda para filtrar (ej: "SOLES")
        only_with_email: Si True, filtra solo registros con email
    
    Returns:
        pd.DataFrame filtrado
    """
    df = df_final.copy()
    
    if filter_empresa:
        df = df[df['EMPRESA'] == filter_empresa]
    
    if filter_moneda:
        df = df[df['MONEDA'] == filter_moneda]
    
    if only_with_email:
        df = df[df['EMAIL_FINAL'] != ""]
    
    return df


def create_synthetic_client_group_email(df_filtered):
    """
    Simula la agrupación de clientes por email para el tab "Notificaciones Email".
    
    Args:
        df_filtered: DataFrame filtrado (vista actual)
    
    Returns:
        pd.DataFrame agrupado por cliente/email
    """
    client_group = df_filtered[df_filtered['EMAIL_FINAL'] != ""].groupby(
        ['COD CLIENTE', 'EMPRESA', 'EMAIL_FINAL']
    )[['SALDO REAL', 'DETR_PENDIENTE_AMOUNT']].sum().reset_index()
    
    # Filtro: Balance > 0 OR Detraction > 0
    client_group = client_group[
        (client_group['SALDO REAL'] > 0.01) | 
        (client_group['DETR_PENDIENTE_AMOUNT'] > 0.01)
    ]
    
    return client_group


def simulate_email_sent(df_final, email, timestamp=None):
    """
    Simula que se envió un email actualizando el tracking en df_final.
    
    Args:
        df_final: DataFrame SSOT
        email: Email que se "envió"
        timestamp: Timestamp del envío (default: now)
    
    Returns:
        pd.DataFrame con tracking actualizado
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    df = df_final.copy()
    mask = df['EMAIL_FINAL'] == email
    df.loc[mask, 'ESTADO_EMAIL'] = 'ENVIADO'
    df.loc[mask, 'FECHA_ULTIMO_ENVIO'] = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    
    return df


# Fixtures predefinidos para tests comunes
def fixture_fresh_load():
    """Fixture: Nuevo ciclo con tracking limpio"""
    return create_synthetic_df_final(num_records=20, with_emails=True, with_duplicates=False)


def fixture_with_duplicates():
    """Fixture: Datos con emails duplicados"""
    return create_synthetic_df_final(num_records=15, with_emails=True, with_duplicates=True)


def fixture_mixed_debt():
    """Fixture: Mix de clientes con/sin deuda y detracciones"""
    return create_synthetic_df_final(num_records=25, with_emails=True, with_duplicates=False)
