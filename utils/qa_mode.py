
import logging

def resolve_recipients(original_email, qa_config):
    """
    Resuelve los destinatarios finales basándose en el modo QA.
    
    Args:
        original_email (str): El correo del cliente real.
        qa_config (dict): Configuración actual de QA.
                          {
                              'enabled': bool,
                              'mode': 'ALL' | 'PRIMARY',
                              'recipients': [list of emails],
                              'allowlist': [list of domains] (optional)
                          }
    
    Returns:
        tuple: (final_email_list, status_msg, is_qa_override)
               final_email_list (list): Lista de correos a enviar.
               status_msg (str): Razón de la decisión.
               is_qa_override (bool): True si se aplicó override QA.
    """
    if not qa_config.get('enabled', False):
        return [original_email], "Production Mode", False

    # QA Mode ON
    qa_recipients = qa_config.get('recipients', [])
    if not qa_recipients:
        # Fallback safety
        return [], "QA Blocked: No QA recipients defined", True

    mode = qa_config.get('mode', 'ALL')
    
    if mode == 'PRIMARY':
        # Send only to the first one
        final_list = [qa_recipients[0]]
        status = f"QA Override (Primary): {qa_recipients[0]}"
    else:
        # Send to ALL
        final_list = qa_recipients
        status = f"QA Override (All): {', '.join(qa_recipients)}"

    return final_list, status, True

def modify_subject_for_qa(subject):
    """Prefija el asunto para QA."""
    return f"[QA - MARCHA BLANCA] {subject}"

def get_qa_banner_html():
    """Retorna el HTML del banner de advertencia para QA."""
    return """
    <div style="background-color: #ffcccc; color: #cc0000; padding: 10px; text-align: center; border-bottom: 2px solid #cc0000; font-weight: bold; font-family: sans-serif;">
        🛠️ PRUEBA INTERNA – NO ES NOTIFICACIÓN REAL 🛠️
    </div>
    """
