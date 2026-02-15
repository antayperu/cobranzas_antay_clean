# Backlog Priorizado - ReporteCobranzas Antay

**Última actualización:** 2026-02-14  
**Versión actual:** v1.5.6  
**Integración Supabase:** 40%

---

## 🔴 Prioridad CRÍTICA (Sprint Actual - Febrero 2026)

### SUPABASE-001: Migración de Datos Notion → Supabase
- **Estado:** 🟡 Pendiente
- **Esfuerzo:** 8 puntos (2-3 días)
- **Dependencias:** Ninguna
- **Asignado:** Por definir
- **Descripción:** Migrar datos de clientes y documentos desde Notion a tablas de Supabase
- **Valor de Negocio:** ALTO - Habilita persistencia en la nube y reduce dependencia de Notion API
- **Criterios de Aceptación:**
  - [ ] Tabla `clientes` poblada desde Notion con todos los campos
  - [ ] Tabla `documentos` poblada desde Notion con relaciones FK
  - [ ] Script de sincronización bidireccional funcionando
  - [ ] Tests de integridad de datos (100% de registros migrados)
  - [ ] Documentación de proceso de migración
- **Notas Técnicas:**
  - Usar `utils/notion_reader.py` como base
  - Implementar en `scripts/migrate_notion_to_supabase.py`
  - Considerar migración incremental para datasets grandes

---

### CODE-001: Refactorizar app.py (Eliminar Código Espaguetti)
- **Estado:** 🟢 En Progreso
- **Esfuerzo:** 5 puntos (1-2 días)
- **Dependencias:** Ninguna
- **Asignado:** En ejecución
- **Descripción:** Reducir complejidad de app.py de 2,395 líneas a ~1,500 líneas
- **Valor de Negocio:** MEDIO - Mejora mantenibilidad y facilita colaboración
- **Criterios de Aceptación:**
  - [x] Eliminar backups manuales y archivos duplicados
  - [x] Actualizar `.gitignore`
  - [ ] Consolidar CSS inline en `utils/ui/styles.py`
  - [ ] Consolidar lógica de Session Recovery (eliminar duplicados)
  - [ ] Extraer configuración de tabs a módulo separado
  - [ ] Tests de regresión pasando (todos los existentes)
  - [ ] Reducción de líneas verificada (objetivo: -900 líneas)
- **Progreso:**
  - ✅ Fase 1: Limpieza de archivos (Completado)
  - 🔄 Fase 2: Refactorización de app.py (En progreso)

---

## 🟠 Prioridad ALTA (Próximo Sprint - Marzo 2026)

### SUPABASE-002: Storage de Archivos e Imágenes
- **Estado:** 🟡 Pendiente
- **Esfuerzo:** 5 puntos (1-2 días)
- **Dependencias:** SUPABASE-001
- **Descripción:** Migrar logos, imágenes generadas y exports a Supabase Storage
- **Valor de Negocio:** MEDIO - Centraliza assets y habilita compartir entre usuarios
- **Criterios de Aceptación:**
  - [ ] Bucket `logos` creado en Supabase Storage
  - [ ] Bucket `exports` creado para archivos Excel/PDF
  - [ ] Bucket `whatsapp-images` para imágenes generadas
  - [ ] Migrar logos existentes desde `assets/`
  - [ ] Actualizar `image_processor.py` para usar Storage
  - [ ] Actualizar `excel_export.py` para guardar en Storage
- **Notas Técnicas:**
  - Configurar políticas de acceso (RLS)
  - Implementar cleanup de archivos antiguos (>30 días)

---

### CONFIG-001: Configuración en Supabase
- **Estado:** 🟡 Pendiente
- **Esfuerzo:** 3 puntos (1 día)
- **Dependencias:** SUPABASE-001
- **Descripción:** Migrar `config.json` a tabla `configuraciones` en Supabase
- **Valor de Negocio:** MEDIO - Permite configuración por usuario y versionado
- **Criterios de Aceptación:**
  - [ ] Tabla `configuraciones` creada con esquema
  - [ ] Migrar configuración actual de `config.json`
  - [ ] Actualizar `settings_manager.py` para leer/escribir en Supabase
  - [ ] Soporte para configuración por usuario
  - [ ] Historial de cambios de configuración
- **Esquema propuesto:**
  ```sql
  CREATE TABLE configuraciones (
    id UUID PRIMARY KEY,
    user_id TEXT,
    key TEXT NOT NULL,
    value JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
  );
  ```

---

### SYNC-001: Sincronización Bidireccional Notion ↔ Supabase
- **Estado:** 🟡 Pendiente
- **Esfuerzo:** 8 puntos (2-3 días)
- **Dependencias:** SUPABASE-001
- **Descripción:** Sistema de sincronización automática entre Notion y Supabase
- **Valor de Negocio:** ALTO - Mantiene ambos sistemas actualizados
- **Criterios de Aceptación:**
  - [ ] Webhook de Notion para detectar cambios
  - [ ] Job programado para sync cada N horas
  - [ ] Resolución de conflictos (last-write-wins)
  - [ ] Logging de sincronizaciones
  - [ ] Dashboard de estado de sync
- **Consideraciones:**
  - Notion no tiene webhooks nativos - usar polling
  - Implementar con Supabase Edge Functions

---

## 🟡 Prioridad MEDIA (Backlog - Abril 2026)

### TESTING-001: Suite de Tests Automatizados
- **Estado:** 🟡 Pendiente
- **Esfuerzo:** 8 puntos (2-3 días)
- **Descripción:** Crear suite completa de tests unitarios e integración
- **Valor de Negocio:** ALTO - Previene regresiones y mejora calidad
- **Criterios de Aceptación:**
  - [ ] Tests unitarios para todos los módulos en `utils/`
  - [ ] Tests de integración para flujos principales
  - [ ] Coverage mínimo del 70%
  - [ ] CI/CD configurado en GitHub Actions
  - [ ] Tests corriendo en cada PR
- **Módulos prioritarios:**
  1. `supabase_client.py` (crítico)
  2. `db_manager.py` (crítico)
  3. `processing.py` (alto)
  4. `email_sender.py` (alto)
  5. `whatsapp_sender.py` (alto)

---

### DOCS-001: Documentación de API y Arquitectura
- **Estado:** 🟡 Pendiente
- **Esfuerzo:** 3 puntos (1 día)
- **Descripción:** Documentar endpoints, funciones y arquitectura del sistema
- **Valor de Negocio:** MEDIO - Facilita onboarding y mantenimiento
- **Criterios de Aceptación:**
  - [ ] README.md actualizado con arquitectura
  - [ ] Docstrings en todos los módulos principales
  - [ ] Diagramas de arquitectura (Mermaid)
  - [ ] Guía de contribución
  - [ ] Documentación de API en Notion
- **Herramientas:**
  - Sphinx para generar docs
  - Mermaid para diagramas

---

### PERF-001: Optimización de Performance
- **Estado:** 🟡 Pendiente
- **Esfuerzo:** 5 puntos (1-2 días)
- **Descripción:** Optimizar carga de datos y procesamiento
- **Valor de Negocio:** MEDIO - Mejora experiencia de usuario
- **Criterios de Aceptación:**
  - [ ] Cachear resultados de Notion (Redis/Supabase)
  - [ ] Lazy loading de datos grandes
  - [ ] Optimizar queries de Supabase (índices)
  - [ ] Reducir tiempo de carga inicial <3s
  - [ ] Profiling de performance
- **Métricas objetivo:**
  - Carga inicial: <3 segundos
  - Filtrado: <500ms
  - Exportación Excel: <2 segundos

---

## 🟢 Prioridad BAJA (Futuro - Mayo+ 2026)

### FEATURE-001: Dashboard de Analytics
- **Estado:** 🟡 Pendiente
- **Esfuerzo:** 13 puntos (3-5 días)
- **Descripción:** Dashboard interactivo de métricas de envío y cobranza
- **Valor de Negocio:** MEDIO - Insights de negocio
- **Criterios de Aceptación:**
  - [ ] Gráficos de envíos por día/semana/mes
  - [ ] Tasa de apertura de emails
  - [ ] Tasa de respuesta de WhatsApp
  - [ ] Efectividad de cobranza por canal
  - [ ] Exportar reportes de analytics
- **Stack tecnológico:**
  - Plotly/Altair para gráficos
  - Supabase para queries agregadas

---

### FEATURE-002: Notificaciones Push en Tiempo Real
- **Estado:** 🟡 Pendiente
- **Esfuerzo:** 8 puntos (2-3 días)
- **Descripción:** Sistema de notificaciones en tiempo real para eventos importantes
- **Valor de Negocio:** BAJO - Nice to have
- **Criterios de Aceptación:**
  - [ ] Notificaciones de nuevos pagos
  - [ ] Alertas de documentos vencidos
  - [ ] Notificaciones de errores de envío
  - [ ] Configuración de preferencias de notificación
- **Tecnología:**
  - Supabase Realtime
  - Streamlit toast notifications

---

### FEATURE-003: Modo Multi-Tenant
- **Estado:** 🟡 Pendiente
- **Esfuerzo:** 13 puntos (3-5 días)
- **Descripción:** Soporte para múltiples empresas/usuarios
- **Valor de Negocio:** ALTO (futuro) - Escalabilidad
- **Criterios de Aceptación:**
  - [ ] Autenticación de usuarios (Supabase Auth)
  - [ ] Aislamiento de datos por tenant
  - [ ] Roles y permisos (admin, usuario, viewer)
  - [ ] Dashboard de administración
- **Consideraciones:**
  - Requiere rediseño de esquema de BD
  - RLS policies en Supabase

---

## 📊 Resumen de Prioridades

| Prioridad | Tareas | Puntos Totales | Tiempo Estimado |
|-----------|--------|----------------|-----------------|
| 🔴 CRÍTICA | 2 | 13 | 3-5 días |
| 🟠 ALTA | 3 | 16 | 4-7 días |
| 🟡 MEDIA | 3 | 16 | 4-7 días |
| 🟢 BAJA | 3 | 34 | 8-13 días |
| **TOTAL** | **11** | **79** | **19-32 días** |

---

## 🎯 Roadmap Sugerido

### Sprint 1 (Febrero 2026) - Fundamentos
- CODE-001: Refactorizar app.py ✅ En progreso
- SUPABASE-001: Migración de datos

### Sprint 2 (Marzo 2026) - Storage y Config
- SUPABASE-002: Storage de archivos
- CONFIG-001: Configuración en Supabase
- SYNC-001: Sincronización Notion

### Sprint 3 (Abril 2026) - Calidad
- TESTING-001: Suite de tests
- DOCS-001: Documentación
- PERF-001: Optimización

### Sprint 4+ (Mayo 2026) - Features Avanzados
- FEATURE-001: Dashboard Analytics
- FEATURE-002: Notificaciones Push
- FEATURE-003: Multi-Tenant

---

## 📝 Notas Generales

### Definición de Esfuerzo (Story Points)
- 1-2 puntos: Tarea simple (< 4 horas)
- 3-5 puntos: Tarea media (1-2 días)
- 8 puntos: Tarea compleja (2-3 días)
- 13 puntos: Tarea muy compleja (3-5 días)
- 21+ puntos: Epic (dividir en tareas más pequeñas)

### Estados
- 🟢 En Progreso
- 🟡 Pendiente
- 🔴 Bloqueado
- ✅ Completado

---

**Última actualización:** 2026-02-14  
**Próxima revisión:** 2026-02-21
