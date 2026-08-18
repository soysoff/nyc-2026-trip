# NYC 2026 — Contexto del proyecto

App familiar para el viaje a Nueva York del **16 al 23 de septiembre de 2026**.
Este archivo resume qué es, cómo está hecho, por qué se tomó cada decisión y qué falta.

> **Estado al 18 de agosto de 2026:** la app está desplegada, funcionando y verificada en navegador real. Todo lo listado abajo está construido; no queda nada a medias. Lo que sigue son decisiones de contenido de la familia (precios de transporte, confirmar el tranvía) más ideas opcionales.

---

## 1. Qué es

Una web app (PWA) donde las 8 personas del viaje ven y editan el mismo plan en vivo. Se abre con un link, sin instalar nada y sin crear cuenta.

- **Días** — itinerario tipo calendario: se desliza horizontalmente para cambiar de día (o con las flechas ‹ › y la tira de fechas), y las actividades se reordenan arrastrando el `⠿`. Entre tarjeta y tarjeta aparece el tramo a pie, y arriba el total del día.
- **Mapa** — mapa real de NYC (tiles claros de CartoDB), pines por categoría, filtros por día y por tipo. Al elegir un día se dibuja la ruta punteada en orden con los pines numerados y un resumen del recorrido.
- **Presupuesto** — total del viaje, costo por persona, desglose por día y turismo vs comida.
- **Actividad** — feed de quién agregó o marcó qué.
- **Notificaciones push** reales al celular cuando alguien cambia algo.
- **Botón 🧭 "Cómo llegar"** en cada tarjeta y en el popup del mapa: abre Google Maps en modo transporte público.
- **Agregar puntos propios** con el botón `+`: nombre, día, categoría, costo, horario, zona, notas y ubicación marcable en un mini-mapa.
- Tocar el título **NYC 2026** vuelve al calendario desde cualquier vista.

### Integrantes
Gaby, Adolfo, Nancy, Sofi, Tefa, Ale, Dinhora, Luis. Cada uno tiene un color asignado en la tabla `members`.
No hay login real: al abrir por primera vez cada quien toca su nombre y se guarda en `localStorage` de ese dispositivo. Sirve para atribuir cambios, no para seguridad.

### Categorías e iconos
La división que pidió Sofi: **todo lo de comida comparte el mismo color naranja** para distinguirlo de un vistazo en el mapa, y el emoji da el detalle.

| Turismo | | Comida (todas en naranja) | |
|---|---|---|---|
| 🗼 landmark | ícono / monumento | 🍽️ restaurant | restaurante |
| 🖼️ museum | museo | 🧁 bakery | bakery / postre |
| 🌳 park | parque | 🥡 streetfood | callejera / casual |
| 🛍️ shopping | shopping | | |
| 🎟️ show | show / evento | | |
| ⛴️ transit | transporte / ferry | | |

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

**Fuente original de los datos:** un Google Sheet de la familia con actividades, costos, horarios y "restaurante cercano" por día. Ese sheet ya fue volcado a la base; **ahora la base es la fuente de verdad** — editar el sheet ya no cambia nada.

Al volcarlo se hicieron dos cosas que no estaban en el sheet: la columna "restaurante cercano" se convirtió en **puntos de comida independientes** (con su propio pin), y se geocodificaron las coordenadas de cada lugar.

### El itinerario hoy

| Día | Lugares | Zona | Costo/persona |
|---|---|---|---|
| Mié 16 sep | 10 | Midtown | $22 |
| Jue 17 sep | 5 | Central Park & UES | $42 |
| Vie 18 sep | 3 | Midtown | $42 |
| Sáb 19 sep | 2 | Upper West Side | $52 |
| Dom 20 sep | 10 | Financial District · Harbor | $43 |
| Lun 21 sep | 8 | Brooklyn · Chelsea · LES | $20 |
| Mar 22 sep | 6 | Outlet · Chinatown · Midtown | $82 |
| Mié 23 sep | 1 | salida | $0 |
| Por confirmar | 1 | Roosevelt Island | — |

**Total: $303 por persona · $2.424 entre los 8** (sin transporte).

Cuatro lugares no tienen coordenadas y por eso no salen en el mapa, sólo en Días y Presupuesto: Empire State, Estatua de la Libertad, el outlet (Woodbury Common, a ~1h de la ciudad) y su food court.

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

### Rutas y tiempos de caminata
Cada día muestra su recorrido: en el mapa, una línea punteada que une los lugares en el orden del itinerario con los pines numerados; en la vista de días, un tramo entre tarjeta y tarjeta (`🚶 ~8 min · 630 m`) y el total del día.

**Los tiempos son estimados y se calculan en el dispositivo**, no con una API: distancia en línea recta (Haversine) multiplicada por 1.28 para compensar que Manhattan se camina en rejilla y no en diagonal, a ~4.8 km/h. Si un tramo pasa de 1.5 km se marca como "mejor en metro".

Se evaluó usar la API pública de OSRM y se descartó: su servidor demo ignora el perfil peatonal (devuelve lo mismo para `foot`, `driving`, `bike`) y no ofrece garantías de disponibilidad. Para el dato real de metro está el enlace directo a Google Maps en cada tramo y en cada lugar (`travelmode=transit`), que no cuesta nada ni requiere llave. Si algún día se quieren tiempos reales de transporte dentro de la app, haría falta una llave de Google Directions API con facturación activada.

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

**Estilo visual.** La primera versión fue Y2K/cyberpunk neón; se descartó a pedido de Sofi, que mandó referencias de apps limpias y modernas. La dirección actual sale de ahí: fondo crema `#F6F2EA`, tarjetas blancas muy redondeadas, tipografía Plus Jakarta Sans bold, color plano por categoría, barra de navegación negra flotante en píldora. Nada de neón, gradientes ni scanlines.

**Tokens de color.**
`--bg #F6F2EA` · `--paper #FFF` · `--ink #171416` · `--ink-soft #5B5560`
Acentos: azul `#3B55E8`, violeta `#8654F0`, verde `#2E9E5B`, amarillo `#F0AE2E`, coral `#FF5C45`, teal `#0FA99A`, naranja `#FF8A3D` (comida).

**Movimiento.** Hay un sistema de animaciones deliberado: entrada escalonada de tarjetas *sólo en la primera carga*, pines que caen al mapa, barras del presupuesto que crecen, sheet que sube, "pop" al marcar visitado, la pestaña activa se expande y muestra su nombre. Todo respeta `prefers-reduced-motion`. La regla importante: **un re-render por sincronización nunca debe animar**, porque se lee como parpadeo (ver bugs).

**Mapa minimalista.** Se cambió de los tiles estándar de OpenStreetMap a **CartoDB Positron** (grises claros) para que los pines de color sean lo único que resalte.

---

## 5. Bugs encontrados y arreglados

Vale la pena dejarlos escritos porque son sutiles y podrían volver:

- **El drag no guardaba el orden.** `persistOrder` usaba `sb.from('pois').upsert(...)` con solo `id` y `order_index`. Un upsert parcial intenta INSERT y choca con las columnas NOT NULL (`day`, `zone`, `category`, `name`), fallando en silencio. Ahora se hace un `update` por fila.
- **El drag se cortaba tras mover una posición.** Se usaba `setPointerCapture` sobre el handle, pero el handle vive dentro de la tarjeta; al reordenar movemos esa tarjeta en el DOM, lo que libera la captura y mata el seguimiento. Ahora los listeners de `pointermove`/`pointerup` van en `document`.
- **Parpadeo al soltar una tarjeta arrastrada.** Al guardar el nuevo orden, Supabase Realtime nos devolvía nuestros propios `UPDATE` y el handler llamaba `renderDays()`, redibujando toda la lista (con su animación de entrada) justo después de soltar. Ahora se comparan los campos visibles: si el evento entrante ya coincide con el estado local, se sincroniza el objeto en silencio y no se redibuja. Además, marcar "visitado" parchea sólo esa tarjeta en lugar de re-renderizar, y la animación de entrada corre únicamente en la primera carga.
- **El mapa se montaba encima de la barra, el FAB y los modales.** Leaflet usa z-index internos de hasta 1000 para sus panes y controles, muy por encima de los de la app (40–50). Se resolvió dándole a `#leaflet-map` su propio contexto de apilamiento (`position:relative; z-index:0; isolation:isolate`), que encierra todos esos valores.
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

> ⚠️ **Vercel NO despliega solo al hacer push.** Al enlazar el proyecto, Vercel no pudo conectarse al repo de GitHub (pidió permisos de admin sobre el repo). El deploy es **manual**: `vercel --prod --yes`. Si algún día se quiere deploy automático, hay que importar el repo desde vercel.com.

Para tocar la base de datos se usan las herramientas MCP de Supabase (`execute_sql`, `apply_migration`, `deploy_edge_function`) sobre el proyecto `ppeiyhgwrbrisnvxyyyc`.

### Cómo se verifica
**Al probar cambios, abrir la app en un navegador real** (Playwright con Chrome headless), no sólo asumir que funciona: casi todos los bugs de arriba sólo se veían corriendo la app de verdad. Lo que ha servido:

- Escuchar `console` y `pageerror` para detectar errores silenciosos.
- Comparar geometría con `getBoundingClientRect()` y `elementFromPoint()` para problemas de superposición y scroll.
- Instrumentar funciones (`window.renderDays = contar(...)`) para probar que algo **no** se ejecuta de más.
- Recargar la página después de una acción para confirmar que se guardó en la base, no sólo en pantalla.

**Ojo:** las pruebas escriben en la base de producción (no hay entorno de staging). Después de probar drags o checks, hay que **restaurar los datos** con `execute_sql` — durante el desarrollo se hizo varias veces.

---

## 7. Pendientes

### Decisiones de la familia (no son trabajo de código)
- **Transporte:** llenar costos y horarios cuando se sepan. Los campos ya existen en cada tarjeta y son editables por cualquiera; hoy no suman al total.
- **Tranvía de Roosevelt Island:** venía incompleto en el sheet, está en el bucket "Por confirmar".
- **Estatua de la Libertad:** decidir entre Staten Island Ferry (gratis, el barco naranja) o Castle Clinton ($25).
- **Orden del 20 de sep:** suma ~6 km zigzagueando por el Financial District aunque todo está cerca. Ahora que los tramos se ven, conviene reordenarlo arrastrando para acortarlo.

### Ideas opcionales
- Tiempos reales de metro dentro de la app → requiere llave de Google Directions API con facturación activada (Google regala $200/mes; este uso costaría $0, pero hay que registrar tarjeta).
- Subir fotos por punto.
- Marcar quién quiere ir a qué (votación por lugar).
- Deploy automático conectando el repo desde vercel.com.
