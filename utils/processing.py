import pandas as pd
import numpy as np
from datetime import date

def format_phone(phone):
    """
    Formatea el teléfono al estándar +51XXXXXXXXX.
    Elimina espacios, guiones y paréntesis.
    Si es NaN o vacío, devuelve "".
    """
    if pd.isna(phone) or phone == "":
        return ""
    
    # Convertir a string y limpiar caracteres no numéricos
    p = str(phone).strip()
    p = ''.join(filter(str.isdigit, p))
    
    if not p:
        return ""
    
    # Si ya empieza con 51 y tiene longitud correcta (11 dígitos: 51 + 9 dígitos)
    if p.startswith("51") and len(p) == 11:
        return "+" + p
    
    # Si es un celular de 9 dígitos, agregar +51
    if len(p) == 9:
        return "+51" + p
        
    # Otros casos (fijos o mal formados), devolver limpio con +51 si parece razonable, o dejar como está si es raro
    # Regla simple solicitada: +51 + X
    if not p.startswith("51"):
        return "+51" + p
    
    return "+" + p

def format_client_code(code):
    """
    Formatea el código de cliente a 6 dígitos con ceros a la izquierda.
    """
    if pd.isna(code):
        return "000000"
    try:
        return str(int(float(code))).zfill(6)
    except:
        return str(code).zfill(6)

def load_data(file_ctas, file_cartera, file_cobranza):
    """
    Carga los 3 DataFrames desde los archivos subidos.
    Maneja excepciones de carga.
    """
    try:
        df_ctas = pd.read_excel(file_ctas)
        df_cartera = pd.read_excel(file_cartera)
        df_cobranza = pd.read_excel(file_cobranza)
        return df_ctas, df_cartera, df_cobranza, None
    except Exception as e:
        return None, None, None, str(e)

def process_data(df_ctas, df_cartera, df_cobranza):
    """
    Aplica la lógica de negocio para fusionar y calcular campos.
    """
    # 1. Estandarizar claves de cruce
    # CtasxCobrar: codcli
    # Cartera: codigo_cliente
    
    # Asegurar tipos string para cruce
    if 'codcli' in df_ctas.columns:
        df_ctas['codcli_key'] = df_ctas['codcli'].apply(format_client_code)
    else:
        raise ValueError("Columna 'codcli' no encontrada en CtasxCobrar")
    
    # --- FILTRO 1: Remover 'tipped' == 'PAV' ---
    if 'tipped' in df_ctas.columns:
        # Normalizar para asegurar consistencia
        df_ctas = df_ctas[df_ctas['tipped'].astype(str).str.strip().str.upper() != 'PAV'].copy()
    else:
        # Si no existe la columna, ¿advertir? Asumimos que continua sin filtrar para no romper.
        pass

    # Buscar columna en Cartera (codigo_cliente o codcli)
    col_cartera_key = 'codigo_cliente'
    if 'codcli' in df_cartera.columns:
        col_cartera_key = 'codcli'
    elif 'codigo_cliente' not in df_cartera.columns:
        raise ValueError("Columna 'codigo_cliente' no encontrada en Cartera")
        
    df_cartera['codcli_key'] = df_cartera[col_cartera_key].apply(format_client_code)
    
    # 2. Cruce Ctas con Cartera (Left Join para mantener todas las cuentas)
    # Traer telefono
    if 'telefono' not in df_cartera.columns:
        df_cartera['telefono'] = ""
    
    # Validar Columna EMAIL (Flexible)
    col_email = None
    for c in df_cartera.columns:
        if str(c).upper().strip() in ['EMAIL', 'CORREO', 'E-MAIL', 'CORREO_ELECTRONICO', 'MAIL']:
            col_email = c
            break
            
    if col_email:
        df_cartera['EMAIL_FINAL'] = df_cartera[col_email].astype(str).str.strip().str.lower()
        # Limpiar 'nan' strings
        df_cartera['EMAIL_FINAL'] = df_cartera['EMAIL_FINAL'].replace({'nan': '', 'nat': '', 'none': ''})
    else:
        df_cartera['EMAIL_FINAL'] = ""

    df_merged = pd.merge(
        df_ctas, 
        df_cartera[['codcli_key', 'telefono', 'EMAIL_FINAL']], 
        on='codcli_key', 
        how='left'
    )
    
    # Formatear teléfono
    df_merged['TELÉFONO'] = df_merged['telefono'].apply(format_phone)
    
    # 3. Construir Comprobante SUNAT (Relación con Cobranza)
    # Regla: Preferir Ctas["Documento Referencia"], si no sersun + "-" + numsun (padding 8)
    def clean_numsun(val):
        try:
            return str(int(float(val))).zfill(8)
        except:
            return str(val).zfill(8)

    def build_comprobante(row):
        # Regla: sersun + "-" + numsun (padding 8)
        # Se ignora "Documento Referencia" del excel para automatizar desde ERP
        sersun = str(row.get("sersun", "")).strip()
        numsun = clean_numsun(row.get("numsun", ""))
        return f"{sersun}-{numsun}"

    df_merged['COMPROBANTE'] = df_merged.apply(build_comprobante, axis=1)
    
    # --- PROCESAMIENTO CLAVE DE CRUCE (MATCH_KEY) ---
    # Usuario solicita: 
    # Ctas: coddoc + sersun + numsun
    # Cobranza: coddoc + numsun
    # Objetivo: Match perfecto
    
    def clean_key_part(val):
        # Normalización robusta: Quitar espacios y guiones para evitar desfases
        return str(val).strip().replace("-", "").replace(" ", "")

    def pad_numsun(val):
        # Asegurar 8 dígitos para el número
        try:
            return str(int(float(val))).zfill(8)
        except:
            # Si no es numérico, intentamos limpiar y rellenar si es corto, o dejar tal cual
            s = str(val).strip()
            if len(s) < 8 and s.isdigit():
                return s.zfill(8)
            return s
    
    def build_match_key_ctas(row):
        # Concatenación robusta con padding en el número
        # Cod + Serie + Num(8)
        return clean_key_part(row.get('coddoc', '')) + clean_key_part(row.get('sersun', '')) + pad_numsun(row.get('numsun', ''))
        
    df_merged['MATCH_KEY'] = df_merged.apply(build_match_key_ctas, axis=1)

    # 4. Calcular Detracción y Estado (Cruce con Cobranza)
    # En Cobranza, clave ahora será MATCH_KEY (coddoc + numsun)
    
    def build_match_key_cobranza(row):
        # Concatenación robusta
        return clean_key_part(row.get('coddoc', '')) + clean_key_part(row.get('numsun', ''))
    
    if 'numsun' not in df_cobranza.columns:
         # Intentar normalizar si se llama diferente, pero prompt dice numsun
         pass
    
    # Preparar tabla de Cobranzas DT
    # Filtrar solo 'DT'
    if 'forpag' in df_cobranza.columns:
        df_dt = df_cobranza[df_cobranza['forpag'] == 'DT'].copy()
    else:
        df_dt = pd.DataFrame() # Si no hay columna forpag, no hay DTs
        
    # Agrupar por numsun para evitar duplicados si hubo pagos parciales DT (aunque raro en detracción)
    # Regla: "Si SÍ existe registro DT -> mostrar cadena legible"
    # Tomamos el último pago DT si hubiera varios
    
    if not df_dt.empty:
        # Asegurar formato de clave en Cobranza
        df_dt['MATCH_KEY'] = df_dt.apply(build_match_key_cobranza, axis=1)
        
        # Crear texto formateado detallado con saltos de línea (para Excel con ajuste de texto)
        # Campos: codbco, nombco, fecpro, mondoc, monpag, forpag, nudopa
        def format_dt_info(row):
            fec = pd.to_datetime(row.get('fecpro', '')).strftime('%d/%m/%Y') if pd.notna(row.get('fecpro')) else ''
            
            # Formatear montos con coma y 2 decimales para el texto (ojo: esto es texto para leer, no numero para sumar)
            try:
                m_doc = f"{float(row.get('mondoc', 0)):,.2f}"
                m_pag = f"{float(row.get('monpag', 0)):,.2f}"
            except:
                m_doc = str(row.get('mondoc', ''))
                m_pag = str(row.get('monpag', ''))

            return (f"Banco: {row.get('nombco', '')} ({row.get('codbco', '')})\n"
                    f"Fecha: {fec}\n"
                    f"Doc: {m_doc}\n"
                    f"Pag: {m_pag}\n"
                    f"Forma: {row.get('forpag', '')}\n"
                    f"Oper: {row.get('nudopa', '')}")

        df_dt['info_dt'] = df_dt.apply(format_dt_info, axis=1)
        
        # Deduplicar por MATCH_KEY
        dt_lookup = df_dt.groupby('MATCH_KEY')['info_dt'].apply(lambda x: "\n---\n".join(x))
        # Lookup de Monto pagado (Suma por si acaso, aunque debería ser único)
        dt_amount_lookup = df_dt.groupby('MATCH_KEY')['monpag'].sum()
    else:
        dt_lookup = pd.Series(dtype='object')
        dt_amount_lookup = pd.Series(dtype='float')

    # --- NUEVA LÓGICA: AMORTIZACIONES (todo lo que NO sea DT) ---
    if not df_cobranza.empty:
        # Filtrar NO DT y NO DET
        df_amort = df_cobranza[~df_cobranza['forpag'].isin(['DT', 'DET'])].copy()
    else:
        df_amort = pd.DataFrame()
        
    if not df_amort.empty:
        # Usar MATCH_KEY también para amortizaciones
        df_amort['MATCH_KEY'] = df_amort.apply(build_match_key_cobranza, axis=1)
        # Usar la misma función de formato
        df_amort['info_amort'] = df_amort.apply(format_dt_info, axis=1)
        # Agrupar concatenando
        amort_lookup = df_amort.groupby('MATCH_KEY')['info_amort'].apply(lambda x: "\n---\n".join(x))
    else:
        amort_lookup = pd.Series(dtype='object')
        
    # 5. Cálculos Finales en Merged
    
    # Importe Referencial (S/) - antes mondoc
    # Se asume que mondoc viene del excel CtasxCobrar
    if 'mondoc' in df_merged.columns:
        df_merged['Importe Referencial (S/)'] = df_merged['mondoc']
    else:
        # Fallback si no existe, aunque debería
        df_merged['Importe Referencial (S/)'] = 0.0
    
    # Helper detracción (Nueva Lógica con Prioridad Lookup)
    def calc_detraccion_final(row):
        match_key = row['MATCH_KEY']
        
        # 1. Prioridad: Si existe en Cobranza (DT), usar ese monto exacto
        if match_key in dt_amount_lookup.index:
            try:
                # Usar el valor encontrado
                val_dt = float(dt_amount_lookup[match_key])
                return round(val_dt, 0)
            except:
                pass # Fallback a cálculo si falla conversión
        
        # 2. Respaldo: Regla de Negocio (> 700 -> 12%)
        try:
            monto = float(row.get("Importe Referencial (S/)", 0))
            if monto > 700.00:
                return round(monto * 0.12, 0)
            return 0.00
        except:
            return 0.00

    df_merged['DETRACCIÓN'] = df_merged.apply(calc_detraccion_final, axis=1)
    
    # Estado Detracción
    def get_estado_dt(row):
        if row['DETRACCIÓN'] == 0:
            return "No Aplica" 
        
        if row['DETRACCIÓN'] <= 0:
            return "-"

        comprobante = row['COMPROBANTE'] # Visual
        match_key = row['MATCH_KEY'] # Internal key
        
        if match_key in dt_lookup.index:
            return dt_lookup[match_key]
        else:
            return "Pendiente"

    df_merged['ESTADO DETRACCION'] = df_merged.apply(get_estado_dt, axis=1)

    # Columna AMORTIZACIONES
    def get_amortizaciones(row):
        match_key = row['MATCH_KEY']
        # Buscar en amort_lookup
        if match_key in amort_lookup.index:
            return amort_lookup[match_key]
        return "-" # O vacío
    
    df_merged['AMORTIZACIONES'] = df_merged.apply(get_amortizaciones, axis=1)

    # 6. Selección y Ordenamiento de Columnas Finales
    # COD CLIENTE (6 dígitos, texto)
    # EMPRESA (de nomcli)
    # TELÉFONO (+51)
    # FECH EMIS (de fecdoc)
    # FECH VENC (de fecvct)
    # COMPROBANTE (Documento Referencia)
    # MONEDA (de codmnd)
    # TIPO CAMBIO (de tipcam)
    # MONT EMIT (de mododo)
    # Importe Referencial (S/) (de mondoc)
    # DETRACCIÓN
    # ESTADO DETRACCION
    # SALDO (de sldacl)
    
    df_merged['COD CLIENTE'] = df_merged['codcli_key']
    df_merged['EMPRESA'] = df_merged['nomcli']
    df_merged['FECH EMIS'] = pd.to_datetime(df_merged['fecdoc']).dt.date
    df_merged['FECH VENC'] = pd.to_datetime(df_merged['fecvct']).dt.date
    df_merged['MONEDA'] = df_merged['codmnd']
    df_merged['TIPO CAMBIO'] = df_merged['tipcam']
    df_merged['MONT EMIT'] = df_merged['mododo']
    df_merged['MONT EMIT'] = df_merged['mododo']
    df_merged['SALDO'] = df_merged['sldacl']
    
    # Campo Nuevo v3.5
    if 'tipped' in df_merged.columns:
        df_merged['TIPO PEDIDO'] = df_merged['tipped']
    else:
        df_merged['TIPO PEDIDO'] = ""
    
    # Calculo de SALDO REAL
    # Regla:
    # Si ESTADO DETRACCION != "Pendiente" (es decir, ya se pagó/aplicó): Saldo Real = Saldo
    # Si ESTADO DETRACCION == "Pendiente":
    #    Si Moneda == 'SOL': Saldo Real = Saldo - Detracción
    #    Si Moneda == 'USD': Saldo Real = Saldo - (Detracción / Tipo Cambio)
    
    def calc_saldo_real(row):
        saldo = float(row.get('SALDO', 0.0))
        detraccion = float(row.get('DETRACCIÓN', 0.0))
        estado_dt = row.get('ESTADO DETRACCION', '')
        moneda = str(row.get('MONEDA', '')).strip().upper()
        tc = float(row.get('TIPO CAMBIO', 1.0))
        
        # Si no aplica detracción (ej. monto bajo), el saldo real es el saldo
        if detraccion <= 0:
            return saldo

        # Si ya se aplicó la detracción (encontrado en cobranza), el saldo ya considera eso?
        # El usuario dijo: "si en el archivo de cobranza ya se aplico la detracción... no debe afectar el saldo... significa que es un saldo real"
        # "si no existira la aplicación... el saldo real... sera el monto del saldo menos el importe de la detracción"
        
        if estado_dt == "Pendiente":
            # Restar la detracción
            if moneda == 'US$': # Caso Dolares
                 # Detraccion esta en soles, convertir a dolares para restar
                 if tc > 0:
                     deduccion_usd = detraccion / tc
                     return saldo - deduccion_usd
                 else:
                     return saldo # Evitar div0
            else:
                # Caso Soles
                return saldo - detraccion
        else:
            # Estado != Pendiente (Pagado, o info de banco) -> Saldo se mantiene
            return saldo

    df_merged['SALDO REAL'] = df_merged.apply(calc_saldo_real, axis=1)

    # --- EXPERT REFINEMENTS v4.0: Aging & Formatting ---
    
    # 1. DÍAS MORA & ESTADO (Semaforización)
    today = date.today()
    
    def calc_aging(row):
        try:
            venc = row['FECH VENC']
            if pd.isna(venc): return 0, "Indeterminado"
            
            # Ensure venc is date object
            if isinstance(venc, pd.Timestamp): venc = venc.date()
            
            delta = (today - venc).days
            
            # Estado (Semáforo Textual)
            if delta < 0:
                status = "🟢 Por Vencer"
            elif delta <= 8:
                status = "🟡 Gestión Preventiva"
            elif delta <= 30:
                status = "🟠 Gestión Administrativa"
            else:
                status = "🔴 Gestión Pre-Legal"
                
            return delta, status
        except:
            return 0, "Error"

    # Apply aging
    aging_results = df_merged.apply(calc_aging, axis=1, result_type='expand')
    df_merged['DÍAS MORA'] = aging_results[0]
    df_merged['ESTADO DEUDA'] = aging_results[1]

    # 2. Formato Moneda Integrado (Pegar símbolo al valor)
    # Columnas a formatear: MONT EMIT, DETRACCIÓN, SALDO, SALDO REAL
    
    def format_currency_cell(row, col_name):
        try:
            amount = float(row.get(col_name, 0))
            if amount == 0: return "-" # Limpieza visual
            
            # Obtener símbolo
            mon = str(row.get('MONEDA', '')).strip().upper()
            symbol = "S/" if mon.startswith('S') else "$"
            
            return f"{symbol} {amount:,.2f}"
        except:
            return str(row.get(col_name, ""))

    # Crear columnas formateadas para Display (Las numéricas se quedan para cálculos si hicieran falta)
    # Sobreescribimos las columnas para el reporte final directo? 
    # El usuario pidió "pegar como parte de la celda". 
    # Si sobreescribimos, perdemos la capacidad de sumar en Excel numéricamente fácil? 
    # El usuario dijo "el cuadro resultante", implicando lo que ve.
    # Para Excel export, mejor tener strings visuales. 
    
    cols_to_format = ['MONT EMIT', 'DETRACCIÓN', 'SALDO', 'SALDO REAL']
    for col in cols_to_format:
        # Crear columna _DISPLAY para visualización, mantener original numérica para cálculos
        display_col = f"{col}_DISPLAY"
        df_merged[display_col] = df_merged.apply(lambda r: format_currency_cell(r, col), axis=1)

    final_cols = [
        'COD CLIENTE', 'EMPRESA', 'TELÉFONO', 
        'TIPO PEDIDO', 
        'COMPROBANTE', 'FECH EMIS', 'FECH VENC',
        'DÍAS MORA', 'ESTADO DEUDA',
        'MONEDA',
        'MONT EMIT', 'MONT EMIT_DISPLAY',
        'SALDO REAL', 'SALDO REAL_DISPLAY',
        'SALDO', 'SALDO_DISPLAY',
        'DETRACCIÓN', 'DETRACCIÓN_DISPLAY',
        'ESTADO DETRACCION', 
        'AMORTIZACIONES',
        'MATCH_KEY',
        'EMAIL_FINAL'
    ]
    
    # Filtrar solo columnas existentes (por seguridad, aunque deberian estar todas)
    final_cols = [c for c in final_cols if c in df_merged.columns]
    
    return df_merged[final_cols]
