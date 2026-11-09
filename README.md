# Switch 2 Price Tracker Chile — GitHub Actions

Monitor de enlaces directos cada ~10 minutos, umbral estricto < $550.000 CLP, avisos Telegram. No requiere PC encendido, VPS ni Docker.

## Instalación
1. Crear repositorio **público** en GitHub (GitHub Actions estándar gratis). Nunca subir el token.
2. Subir los archivos conservando `.github/workflows/monitor.yml`.
3. En Settings > Secrets and variables > Actions > New repository secret, crear `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`.
4. Editar `config/products.yaml`: poner URLs HTTPS directas y `enabled: true`.
5. En Settings > Actions > General > Workflow permissions seleccionar **Read and write permissions** (necesario para guardar historial), guardar.
6. En Actions > Monitor Switch 2 > Run workflow, iniciar una prueba manual. Leer logs.
7. Las ejecuciones programadas se activan desde la rama principal. Si falla `git push` revisar permisos, protecciones de rama y cambios concurrentes.

## Consideraciones
- GitHub puede retrasar/omitir ejecuciones programadas; en repos públicos desactiva schedule tras 60 días sin actividad.
- Los precios se leen de JSON-LD o metaetiquetas que declaren CLP; **no hay extractores específicos de tiendas probados**. Un mensaje `precio CLP no verificable` significa que requiere adaptación, no que esté sin oferta.
- `state/prices.json` es público: contiene precios y URLs, nunca credenciales.
- El monitor alerta al primer precio bajo umbral o ante una nueva reducción. No notifica continuamente el mismo precio.
- El bot envía mensajes, pero NO responde a comandos `/estado` ni `/precios` en esta versión programada.
- No intenta evadir CAPTCHA, 403 ni 429. Respetar condiciones de acceso y robots.txt.
- Para verificar Telegram independientemente, consultar Bot API `sendMessage` con token y chat ID en un entorno seguro.
