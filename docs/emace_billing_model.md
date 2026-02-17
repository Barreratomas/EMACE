# Modelo de Billing para EMACE con Mercado Pago

## Contexto de Negocio

El sistema implementa:

-   Suscripciones mensuales con renovación automática
-   Primer mes gratis (trial) para TODOS los planes
-   Opción de pago único definitivo (lifetime)
-   El pago definitivo reemplaza cualquier suscripción activa
-   Operación multi-tenant (Vendor-centric)
-   Mercado Pago como procesador de pagos

------------------------------------------------------------------------

## Principio Central del Sistema

El acceso del Vendor NO debe depender directamente de la suscripción,
sino de un estado único:

    ACCESS_MODE = subscription | lifetime

Nunca deben coexistir ambos.

------------------------------------------------------------------------

## Entidad Principal Recomendada

### vendor_access_state

Campos sugeridos:

-   vendor_id
-   access_mode → subscription \| lifetime
-   source → trial \| paid_subscription \| lifetime_purchase
-   valid_until → fecha o NULL para lifetime
-   subscription_id_mp → nullable

Esta entidad es la fuente de verdad del acceso al sistema.

------------------------------------------------------------------------

## Estados Válidos del Vendor

### 1. Trial Activo (Primer Mes Gratis)

    access_mode = subscription
    source = trial
    valid_until = now + 30 días
    subscription_id_mp = NULL

Características:

-   No existe suscripción en Mercado Pago
-   Control total desde backend
-   Scheduler gobierna vencimiento

------------------------------------------------------------------------

### 2. Suscripción Paga Activa

    access_mode = subscription
    source = paid_subscription
    valid_until = current_period_end
    subscription_id_mp = MP_ID

Características:

-   Renovación automática en Mercado Pago
-   Webhooks actualizan estado
-   Backend extiende acceso

------------------------------------------------------------------------

### 3. Lifetime (Pago Definitivo)

    access_mode = lifetime
    source = lifetime_purchase
    valid_until = NULL
    subscription_id_mp = NULL

Características:

-   Sin renovaciones
-   Sin dependencia posterior de Mercado Pago
-   Acceso permanente

------------------------------------------------------------------------

## Regla Crítica del Sistema

Lifetime SIEMPRE domina sobre suscripción.

Si un Vendor compra lifetime:

-   Cancelar suscripción activa en Mercado Pago
-   Limpiar subscription_id_mp
-   Ignorar eventos posteriores de suscripción
-   Cambiar access_mode a lifetime

------------------------------------------------------------------------

## Flujo de Trial

### Alta de cuenta / inicio trial

1.  Vendor crea cuenta
2.  Backend crea vendor_access_state con source = trial
3.  Acceso inmediato sin Mercado Pago

------------------------------------------------------------------------

### Scheduler controla trial

Proceso periódico:

    if now >= valid_until AND source == trial:
        marcar trial_expired
        restringir acceso premium

------------------------------------------------------------------------

## Conversión a Suscripción

1.  Usuario decide pagar
2.  Crear suscripción en Mercado Pago
3.  Guardar subscription_id_mp
4.  Esperar webhook aprobado
5.  Actualizar source = paid_subscription

Nunca activar acceso por frontend.

------------------------------------------------------------------------

## Renovaciones Mensuales

Webhook pago aprobado:

-   Extender valid_until

Webhook pago fallido:

-   Marcar estado past_due

Scheduler define suspensión.

------------------------------------------------------------------------

## Manejo de Pagos Fallidos

Política recomendada:

-   Pago falla → estado past_due
-   +3 días → notificar usuario
-   +5 días → suspender acceso
-   Pago exitoso → restaurar acceso

------------------------------------------------------------------------

## Flujo de Compra Lifetime

1.  Verificar Vendor
2.  Si existe suscripción activa → cancelar en Mercado Pago
3.  Registrar compra
4.  Actualizar vendor_access_state:

```{=html}
<!-- -->
```
    access_mode = lifetime
    valid_until = NULL
    subscription_id_mp = NULL

No esperar cancelación para otorgar acceso.

------------------------------------------------------------------------

## Manejo de Webhooks tras Lifetime

Mercado Pago puede enviar eventos tardíos.

El webhook debe verificar:

    if access_mode == lifetime:
        ignorar eventos de suscripción

Evita reactivar suscripciones accidentalmente.

------------------------------------------------------------------------

## Cambios de Plan (Suscripciones)

Proceso seguro:

1.  Cancelar suscripción actual en Mercado Pago
2.  Crear nueva suscripción
3.  Guardar nuevo subscription_id_mp
4.  Actualizar estado interno

Mercado Pago no prorratea automáticamente.

------------------------------------------------------------------------

## Cancelación de Suscripción

Recomendado:

-   Cancelar en Mercado Pago
-   Mantener acceso hasta valid_until
-   No cortar acceso inmediato

------------------------------------------------------------------------

## Reglas de Diseño Importantes

-   Trial nunca interactúa con Mercado Pago
-   Base de datos = única fuente de verdad
-   Mercado Pago = procesador, no autoridad de acceso
-   Webhooks gobiernan estados de pago
-   ACCESS_MODE determina permisos del sistema

------------------------------------------------------------------------

## UX Recomendada

### Suscripción Mensual

"Primer mes gratis. Luego ARS X / mes. Cancelas cuando quieras."

### Pago Definitivo

"Pago único ARS X. Acceso permanente. Sin cargos futuros."

Evitar ambigüedad para reducir disputas.

------------------------------------------------------------------------

## Estrategia Arquitectónica

Implementar:

-   Trial completamente interno
-   Suscripción solo tras primer pago real
-   Lifetime como override absoluto
-   Estados webhook-driven
-   Scheduler para proactividad

------------------------------------------------------------------------

Fin del documento.
