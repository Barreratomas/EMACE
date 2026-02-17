docker compose up postgres qdrant adminer -d

# Túnel Cloudflared para Webhooks de Mercado Pago (Desarrollo)
docker compose exec backend python manage.py    
## Servicios base (opcional)

```bash
docker compose up -d postgres qdrant adminer
```

## Iniciar backend local (puerto 8000)

```powershell
cd backend
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

## Exponer el backend con Cloudflared

```bash
docker compose up cloudflared -d
docker logs -f agent_cloudflared
```

Busca la URL pública tipo:

```
https://<subdominio>.trycloudflare.com
```

## Variables de entorno (backend/.env)

```env
MP_ACCESS_TOKEN=<<tu_token_mp>>
MP_WEBHOOK_SECRET=<<tu_secreto_webhook>>
MP_WEBHOOK_URL=https://<subdominio>.trycloudflare.com/api/v1/billing/webhooks/mp
```

## Healthcheck del webhook

```bash
curl -s https://<subdominio>.trycloudflare.com/api/v1/billing/webhooks/mp/health
```

Debe responder:

```json
{"status":"ok"}
```

## Registrar webhook en Mercado Pago

- URL: `https://<subdominio>.trycloudflare.com/api/v1/billing/webhooks/mp`
- Eventos recomendados: `payment`, `payment.updated`, `subscription/preapproval`
- Modo: Prueba o Productivo según tu token.

## Prueba rápida

1) Crear preferencia desde el Frontend (Settings → Billing) o vía API:

```bash
curl -X POST http://localhost:8000/api/v1/billing/subscriptions ^
  -H "Authorization: Bearer <ACCESS_TOKEN>" ^
  -H "Content-Type: application/json" ^
  -d "{\"title\":\"Plan Mensual\",\"price\":1.0}"
```

2) Enviar un webhook de prueba (simulado):

```bash
curl -X POST https://<subdominio>.trycloudflare.com/api/v1/billing/webhooks/mp ^
  -H "x-request-id: mp-test-1" ^
  -H "Content-Type: application/json" ^
  -d "{\"type\":\"payment\",\"metadata\":{\"vendor_id\":<VENDOR_ID>}}"
```

## Cierre del túnel

```bash
docker compose down cloudflared
```
