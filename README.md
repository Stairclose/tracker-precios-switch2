# Switch 2 Tracker Chile — v2 (GitHub Actions)

## Estado real de las integraciones
- Mercado Libre: adaptador API `sale_price` implementado; requiere token OAuth válido, permisos y un ID de publicación `MLC...` comprobado. **No se ha probado con credenciales reales**. El token expira y necesita renovación; la renovación automática aún no está implementada.
- Knasta y SoloTodo: entradas preparadas, **sin consulta automática**. No hay integración autorizada verificada; se dejan deshabilitadas.
- HTML genérico: disponible mediante `provider: html` solo para sitios que permiten consultas. No evita 403/429.

## Instalación en GitHub
1. Reemplaza `monitor.py`, `config/products.yaml` y `.github/workflows/monitor.yml` de tu repositorio por los del ZIP. Conserva `state/prices.json` y tus secrets de Telegram.
2. Crea una aplicación en https://developers.mercadolibre.cl/crea-una-aplicacion-en-mercado-libre-es y completa el proceso OAuth 2.0 de autorización según la documentación oficial. **No basta con Client ID y Client Secret**.
3. Añade el token de acceso en `Settings > Secrets and variables > Actions > New repository secret` con nombre `MELI_ACCESS_TOKEN`. No lo publiques.
4. Confirma que `MLC1604534647` corresponde a la publicación y vendedor que deseas vigilar; el ID `MLC49200061` es de catálogo, no una publicación. Modifica `item_id` si corresponde y cambia `enabled: true`.
5. En `Actions > Monitor Switch 2 > Run workflow`, ejecuta y revisa logs. La programación existente es cada 10 minutos aproximadamente.

**IMPORTANTE:** Los access tokens de Mercado Libre suelen expirar tras 6 horas; el refresh token rota y debe guardarse de forma segura. GitHub Actions no renueva el token en esta v2. Para monitorización 24/7 habrá que agregar renovación segura de credenciales, con persistencia protegida, o usar una fuente de precios autorizada sin OAuth. No guardes tokens en el archivo `state/prices.json` ni en el repositorio público.

Si un proveedor no confirma precio en CLP, no se envía alerta. El proyecto no verifica por ahora stock ni descuentos exclusivos por tarjeta.
