# NYC 2026 — Contexto del proyecto

App familiar para el viaje a Nueva York del **16 al 23 de septiembre de 2026**.
Este archivo resume qué es, cómo está hecho, por qué se tomó cada decisión y qué falta.

---

## 1. Qué es

Una web app (PWA) donde las 8 personas del viaje ven y editan el mismo plan en vivo:

- **Días** — itinerario tipo calendario: se desliza horizontalmente para cambiar de día, y las actividades se reordenan arrastrando.
- **Mapa** — mapa real de NYC con un pin por lugar, filtrable por día y por tipo (turismo / comida).
- **Presupuesto** — total del viaje, costo por persona, desglose por día y turismo vs comida.
- **Actividad** — feed de quién agregó o marcó qué.
- **Notificaciones push** reales al celular cuando alguien cambia algo.

### Integrantes
Gaby, Adolfo, Nancy, Sofi, Tefa, Ale, Dinhora, Luis.
No hay login real: al abrir por primera vez cada quien toca su nombre y se guarda en `localStorage` de ese dispositivo. Sirve para atribuir cambios, no para seguridad.

---

## 2. URLs y dónde vive todo

| Qué | Dónde |
|---|---|
| App en producción | https://nyc-2026-trip.vercel.app |
| Espejo | https://soysoff.github.io/nyc-2026-trip/ |
| Repo | https://github.com/soysoff/nyc-2026-trip |
| Proyecto local | `/Users/panorama/Desktop/NY_2026` |
| Backend (Supabase) | proyecto `ny-family-trip`, ref `ppeiyhgwrbrisnvxyyyc`, región us-east-2 |
| Cuenta | soyso.studio@gmail.com (GitHub: `soysoff`, Vercel: `soysostudio`) |

**Fuente original de los datos:** un Google Sheet de la familia con actividades, costos, horarios y "restaurante cercano" por día. Ese sheet ya fue volcado a la base; ahora la base es la fuente de verdad.

---

## 3. Arquitectura

Sin framework y sin build step: **un solo `index.html`** con su CSS y JS embebidos, más `sw.js`, `manifest.json` y dos íconos. Se sirve tal cual, estático.

```
index.html        toda la app (estilos + lógica)
sw.js             service worker (recibe los push)
manifest.json     PWA: nombre, íconos, standalone
icon-192/512.png  íconos
scripts/          build_data.py + pois_seed.json (generaron el seed inicial)
contexto.md       este archivo
```

Dependencias por CDN: **Leaflet** (mapa) y **supabase-js** (datos y realtime). Tipografía: Plus Jakarta Sans (Google Fonts).

### Base de datos (Supabase / Postgres)

- `members` — los 8 nombres + su color.
- `pois` — cada punto: `day`, `zone`, `category`, `name`, `cost`, `schedule`, `transport_cost`, `transport_schedule`, `lat`, `lon`, `notes`, `is_done`, `added_by`, `updated_by`, `order_index`.
- `push_subscriptions` — suscripciones push por dispositivo.
- `activity_log` — alimenta el feed y dispara los push.

**RLS está activo pero las políticas son abiertas a `anon`** (leer y escribir). Es deliberado: es una app familiar privada por link, no un producto público. La seguridad real es que nadie más conoce la URL. Si algún día se abre a más gente, esto hay que cambiarlo.

### Tiempo real
Supabase Realtime (`postgres_changes`) sobre `pois` y `activity_log`. Cualquier cambio aparece en los demás dispositivos sin recargar.

### Notificaciones push
1. El navegador se suscribe con una llave VAPID pública y guarda la suscripción en `push_subscriptions`.
2. Un trigger de Postgres (`notify_poi_change`) se dispara al agregar/marcar/actualizar transporte, escribe en `activity_log` y llama vía `pg_net` a la Edge Function `send-push`.
3. `send-push` (Deno + `npm:web-push`) manda la notificación a todos los dispositivos y limpia suscripciones muertas (404/410).

La llave privada VAPID y el secreto del webhook viven **solo dentro de la Edge Function**, nunca en el frontend.

> **iPhone:** Safari solo permite push si el sitio está agregado a la pantalla de inicio. La app muestra un banner explicándolo cuando detecta ese caso.

---

## 4. Decisiones y por qué

**Por qué no un Artifact de Claude.** Fue el primer intento. Se descartó porque la edición en vivo exigiría que cada familiar tuviera cuenta de claude.ai, y porque un Artifact no puede mandar push real al celular.

**Por qué Vercel y no Supabase Storage / Edge Functions para el frontend.** Se intentaron ambos y fallaron: Supabase sirve todo HTML con `Content-Type: text/plain` y `Content-Security-Policy: default-src 'none'; sandbox` (protección anti-phishing), así que la página nunca ejecuta su JS. Se pasó a GitHub Pages y luego a Vercel, que es donde vive ahora.

**Por qué HTML plano sin framework.** El entorno no tenía Node al empezar (se instaló después, en `~/.local/nodejs`). Sin build step la app es más fácil de mantener y desplegar, y para este tamaño no hace falta más.

**Por qué los costos se guardan por persona.** Así venían en el sheet original. La app muestra `$X /persona` en cada tarjeta y el presupuesto calcula el total multiplicando por 8.

**Por qué el transporte está vacío.** La familia todavía no tiene esos precios/horarios. Los campos existen en cada tarjeta y son editables, pero no suman al total hasta que se llenen.

**Estilo visual.** La primera versión fue Y2K/cyberpunk neón; se descartó a pedido de Sofi por una dirección limpia y moderna: fondo crema, tarjetas blancas, tipografía bold redondeada, color plano por categoría, barra de navegación negra flotante.

---

## 5. Bugs encontrados y arreglados

Vale la pena dejarlos escritos porque son sutiles y podrían volver:

- **El drag no guardaba el orden.** `persistOrder` usaba `sb.from('pois').upsert(...)` con solo `id` y `order_index`. Un upsert parcial intenta INSERT y choca con las columnas NOT NULL (`day`, `zone`, `category`, `name`), fallando en silencio. Ahora se hace un `update` por fila.
- **El drag se cortaba tras mover una posición.** Se usaba `setPointerCapture` sobre el handle, pero el handle vive dentro de la tarjeta; al reordenar movemos esa tarjeta en el DOM, lo que libera la captura y mata el seguimiento. Ahora los listeners de `pointermove`/`pointerup` van en `document`.
- **Parpadeo al soltar una tarjeta arrastrada.** Al guardar el nuevo orden, Supabase Realtime nos devolvía nuestros propios `UPDATE` y el handler llamaba `renderDays()`, redibujando toda la lista (con su animación de entrada) justo después de soltar. Ahora se comparan los campos visibles: si el evento entrante ya coincide con el estado local, se sincroniza el objeto en silencio y no se redibuja. Además, marcar "visitado" parchea sólo esa tarjeta en lugar de re-renderizar, y la animación de entrada corre únicamente en la primera carga.
- **El mapa quedaba debajo de la barra de navegación.** El alto se calculaba como `innerHeight - top`, ignorando que la barra flota encima. Se resta el espacio real de la barra, medido en runtime.
- **Doble scroll raro en mapa y filtros.** Mismo origen: un `padding-bottom` heredado más el alto mal calculado dejaban ~94px de sobra.
- **El día no se precargaba al agregar un punto.** `form.reset()` corría *después* de asignar el día y lo borraba.
- **El presupuesto estaba invertido.** Mostraba el subtotal como total y lo dividía entre 8, cuando los precios ya eran por persona.
- **Avisos de seguridad de Supabase.** `search_path` mutable en la función del trigger, `pg_net` en el esquema `public`, y la función ejecutable por `anon`. Los tres corregidos; el linter de seguridad sale limpio.

---

## 6. Cómo trabajar en esto

```bash
cd /Users/panorama/Desktop/NY_2026
export PATH="$HOME/.local/nodejs/bin:$HOME/.local/bin:$PATH"

# editar index.html y probar abriéndolo en el navegador

git add -A && git commit -m "..." && git push origin main
vercel --prod --yes        # despliega a producción
```

Node vive en `~/.local/nodejs` (instalado sin permisos de administrador). `gh` vive en `~/.local/bin`.

Para tocar la base de datos se usan las herramientas MCP de Supabase (`execute_sql`, `apply_migration`, `deploy_edge_function`) sobre el proyecto `ppeiyhgwrbrisnvxyyyc`.

**Al probar cambios, verificar en un navegador real** (Playwright con Chrome headless), no solo asumir que funciona: varios de los bugs de arriba solo se veían corriendo la app de verdad.

---

## 7. Pendientes / ideas

- Llenar costos y horarios de transporte cuando se sepan, y decidir si suman al total.
- Confirmar el tranvía de Roosevelt Island (hoy está en el bucket "Por confirmar").
- Decidir la opción para la Estatua de la Libertad: Staten Island Ferry (gratis) o Castle Clinton ($25).
- El outlet (Woodbury Common) está fuera del mapa por estar a ~1h de la ciudad; aparece en Días y Presupuesto.
- Posible: subir fotos por punto, o marcar quién quiere ir a qué.
