#!/usr/bin/env python3
"""Test directo de connect_wa_session para debuggear errores"""

import sys
sys.path.insert(0, '.')

try:
    print("[TEST] Iniciando test de connect_wa_session...")
    from utils.whatsapp_sender import connect_wa_session, _PLAYWRIGHT_OK
    
    print(f"[TEST] _PLAYWRIGHT_OK: {_PLAYWRIGHT_OK}")
    
    if not _PLAYWRIGHT_OK:
        print("[ERROR] Playwright no está disponible!")
    else:
        print("[TEST] Intentando conectar WhatsApp (timeout: 10 segundos)...")
        print("[TEST] Esto abrirá Chrome en el servidor...")
        print("[TEST] Escanea el QR con tu teléfono cuando aparezca")
        print("="*60)
        
        ok, phone, profile, err = connect_wa_session(timeout_seconds=10)
        
        print("="*60)
        print(f"\n[RESULT] OK: {ok}")
        print(f"[RESULT] Phone: {phone}")
        print(f"[RESULT] Profile: {profile}")
        if err:
            print(f"[RESULT] Error: {err}")
        
except Exception as e:
    import traceback
    print(f"\n[EXCEPTION] Error durante test:")
    print(traceback.format_exc())
