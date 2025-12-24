
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

def get_qa_banner_html(real_email=None, qa_list=None):
    """Retorna el HTML del banner de advertencia para QA con detalles."""
    details = ""
    if real_email:
        details += f"<div style='font-size:12px; margin-top:5px; color:#666;'>Original Client: {real_email}</div>"
    if qa_list:
        qa_str = ", ".join(qa_list) if isinstance(qa_list, list) else str(qa_list)
        details += f"<div style='font-size:12px; color:#666;'>QA Target: {qa_str}</div>"
        
    return f"""
    <div style="background-color: #fffbdd; color: #856404; padding: 15px; border-bottom: 2px solid #ffeeba; font-family: sans-serif; margin-bottom: 20px;">
        <div style="font-weight: bold; font-size: 14px; text-align: center; color: #d32f2f;">
            ⚠️ PRUEBA INTERNA – MARCHA BLANCA (QA) ⚠️
        </div>
        <div style="text-align: center; font-size: 12px; margin-top: 4px;">
            NO ES NOTIFICACIÓN REAL. NO ENVIAR A CLIENTES.
        </div>
        {details}
    </div>
    """
