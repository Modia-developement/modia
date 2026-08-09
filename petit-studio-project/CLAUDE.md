# Petit Studio (a.k.a. PhotoKid) — Website

## What this is

A single-page marketing/sales website for **Petit Studio**, a newborn/baby portrait
studio that sells AI-generated artistic portraits instead of a traditional photoshoot.
Parents upload a few phone photos of their baby, pick a style, and receive
professionally retouched portraits by email in 24–48h.

Business owner: Alba. Ten years in software (design/product/PM at large digital
companies). Treats AI as a production tool, not the product itself — the brand,
curation, and creative direction are the differentiators. Target: ~€2,000/month
once established. Prefers building/product work over cold outreach.

## Live site

Deployed on Vercel (free tier), account `modia.developement@gmail.com`:
**https://petit-studio-project.vercel.app**

- `/` → serves `petit_studio_v3.html` (via the rewrite in `vercel.json`)
- `/proximamente.html?producto=X` → the waitlist page, same as locally
- `/pedido.html?pack=basic|flex` → the order wizard (Phase 1, see below)
- Redeploy after changes with `npx vercel --prod --yes` from inside
  `petit-studio-project/` (requires being logged into the `modia.developement`
  Vercel account — `npx vercel whoami` to check, `npx vercel login` to switch).
- No custom domain connected yet — the `.vercel.app` URL is what's live.

## Files

```
petit_studio_v3.html    ← main site (single file, self-contained, offline-capable)
proximamente.html       ← "coming soon" waitlist page for features not yet live
pedido.html             ← order wizard — GENERATED, do not edit (see Page 3)
pedido.template.html    ← the wizard's real source; edit this one
build_pedido.py         ← regenerates pedido.html from the template + catalog
vercel.json             ← rewrite so "/" serves petit_studio_v3.html on Vercel
.vercelignore           ← keeps template/build script/CLAUDE.md out of the deploy
CLAUDE.md               ← this file
```

No framework and no package.json. Every page is raw HTML + Tailwind (via CDN
`<script>`) + vanilla JS in inline `<script>` tags, and can be opened straight
from disk in a browser.

The one exception is `pedido.html`: it has a **build step**
(`python3 build_pedido.py`) because its style catalog is generated from
`petit_studio_v3.html` rather than maintained by hand. Edit
`pedido.template.html`, then run the script. See Page 3 below.

⚠️ `petit_studio_v3.html` is ~7 MB because every photo is embedded inline as a
base64 JPEG `data:` URI (no external image files, no `/assets` folder). This is
intentional — see "Why base64 images" below. Expect this file to be slow to open
in a text editor; prefer `grep`/regex-based edits over loading it whole where
possible.

## Why base64 images (do not change this pattern without discussion)

The site was explicitly built to be **fully offline-capable**: Alba downloads
the single `.html` file and it must render correctly — including every photo —
with zero external requests and zero broken links, even if uploaded somewhere
that strips a sibling `/images` folder. Every photo the client is shown in this
project therefore gets embedded as `data:image/jpeg;base64,...` directly in the
`src` attribute, never as a relative file path.

If you add images, follow the existing pipeline (see "Image pipeline" below) —
don't switch to `<img src="photo.jpg">` with a separate file unless Alba asks
for that explicitly (it would break the single-file portability the whole
project is built around).

## Image pipeline (used for every photo added to this site)

Source photos come from an AI portrait-generation tool that stamps a small
4-pointed sparkle/star watermark in the bottom-right corner of every image
(roughly at relative position x≈0.85·width, y≈0.90·height). **Every image added
to this site must have that watermark removed before embedding.** Standing
instruction from Alba (see her memory notes): always remove the watermark,
using inpainting, then optimize for size/quality — every time images are added,
without needing to be asked again.

Pipeline used throughout this project (Python, Pillow + OpenCV):

```python
from PIL import Image, ImageFilter
import numpy as np, cv2, io, base64

def process(path):
    img = Image.open(path).convert('RGB')
    w, h = img.size

    # 1. Inpaint the watermark region (elliptical mask, bottom-right corner)
    mask = np.zeros((h, w), dtype=np.uint8)
    cx, cy = int(w*0.85), int(h*0.90)
    rx, ry = int(w*0.075), int(h*0.06)
    cv2.ellipse(mask, (cx, cy), (rx, ry), 0, 0, 360, 255, -1)
    arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    inpainted = cv2.inpaint(arr, mask, 5, cv2.INPAINT_TELEA)
    result = Image.fromarray(cv2.cvtColor(inpainted, cv2.COLOR_BGR2RGB))

    # 2. Cap resolution for performance (longest side ≤ 1000px is plenty for
    #    the grid/carousel display sizes used on this site)
    maxdim = 1000
    if max(w, h) > maxdim:
        ratio = maxdim / max(w, h)
        result = result.resize((int(w*ratio), int(h*ratio)), Image.LANCZOS)

    # 3. Compensate for inpaint/resize softness
    result = result.filter(ImageFilter.UnsharpMask(radius=1.3, percent=95, threshold=2))

    # 4. Re-encode as optimized JPEG (quality 82–85 is the sweet spot used
    #    throughout — good visual quality, reasonable file size)
    buf = io.BytesIO()
    result.save(buf, format='JPEG', quality=82, optimize=True)
    return base64.b64encode(buf.getvalue()).decode()
```

Notes:
- The watermark position is fairly consistent across source images but not
  pixel-perfect — the ellipse mask has generous margin on purpose. If a new
  batch of images has the watermark in a different position, re-derive the
  mask coordinates by zooming into a sample image's corner before batch
  processing the rest.
- Some source images place body/clothing content near the watermark region —
  inpainting will slightly soften that area. This has been an acceptable
  trade-off so far; flag it to Alba if it's ever visibly bad on a hero-level
  image (e.g. a carousel slide).
- When editing the HTML file to insert/replace a `src="data:image/jpeg;base64,..."`,
  never hand-edit the base64 string — always regenerate it from the source
  image through the pipeline above, then do a scripted string replace. The
  base64 blocks are too long to safely hand-edit or fully re-view in one shot;
  use targeted `re.sub`/`str.replace` on unique surrounding text (alt text,
  data-category, structural HTML) rather than trying to view/diff the whole file.

## Page 1: `petit_studio_v3.html`

Single page, sections in order (all `<section id="...">`):

| id | Content |
|---|---|
| (nav) | Fixed top nav, links to sections below |
| (hero) | Headline + subtitle + CTA button → `#pricing` |
| `beneficios` | 4-card "La Nueva Era del Retrato" benefits grid |
| `stage` | Hero image carousel ("Cómo funciona"-adjacent showcase) — see Carousel below |
| `estilos` | "Nuestros Estilos" — filterable style gallery — see Styles below |
| `pasos` | "Cómo funciona" — 3-step process explainer |
| `pricing` | **Packs digitales** — 3 cards: Basic, Flex, Regala un pack (digital gift) |
| `pricing-print` | **Packs impresos** — 3 cards: Álbum o póster, Pack de imanes, Regala un pack (print gift) |
| `faq` | Accordion FAQ |

### Design system / tokens

```css
body background:       #050508  (near-black)
ambient glow accents:  purple/violet radial gradients, rgba(124,92,196,*) family
glass-panel:           background rgba(255,255,255,.05), backdrop-filter blur(12px),
                        border rgba(255,255,255,.1)
text-glow:              text-shadow 0 0 20px rgba(255,255,255,.3)  — used on headlines
display font:           'Epilogue' (class .f-display)  — headings
body font:               'Manrope' (class .f-body)       — everything else
icons:                   Material Symbols Outlined (rounded, weight 300)
scroll reveal:           .reveal → .reveal.in (IntersectionObserver-driven fade+translateY)
```

Buttons:
- Primary CTA / "Seleccionar" (paid, available packs): solid white bg, black
  text, `bg-white text-black hover:scale-[1.03]` + white glow shadow. **All
  four "Seleccionar"/purchase buttons across both pricing sections must stay
  visually identical** — this was explicitly unified on request; don't let
  them drift apart again.
- "Comprar regalo" (gift cards): stays **purple/lilac**, intentionally distinct
  from the white buttons — `background:rgba(124,80,210,.45); border-color:rgba(170,130,245,.45)`.
  Do not unify these with the white buttons — Alba explicitly asked to keep
  them different.

### Styles gallery (`#estilos`)

Chip-filter UI: clicking a chip (`.chip[data-category="X"]`) shows only
`.gallery-item[data-category="X"]` elements (toggles Tailwind's `hidden` class),
implemented in a plain JS `querySelectorAll` handler near the bottom of the
`<script>` block. Grid container: `<div id="stylesGrid" class="grid grid-cols-2
md:grid-cols-3 gap-4">`.

Current categories, in tab order (first tab is active/visible by default):

| Category (`data-category`) | Photo count | Notes |
|---|---|---|
| **Love** | 20 | Flagship/signature style. Heart-relief fabric backdrop (concave heart shape visible only through light/texture), one baby per solid-color backdrop. Default active tab. |
| **Minimal white** | 10 | White/cream studio backgrounds, editorial/lifestyle poses. |
| **Minimal black** | 10 | Black studio backdrop, dramatic/moody lighting (spotlights, light beams). |
| **Fantasía** | 2 | (formerly "Dreamy Stars") — moon/stars dreamy theme. Untouched since early site version. |
| **Estudio** | 2 | (formerly "Activo") — studio/active poses. Untouched since early site version. |

⚠️ A "Blanco y negro" category and an "Artístico" (watercolor) category both
existed earlier in the project and were **removed** at Alba's request — don't
resurrect them without checking with her first.

Each gallery item is:
```html
<div class="gallery-item aspect-[3/4] rounded-2xl glass-panel p-1.5 overflow-hidden group relative hidden" data-category="CATEGORY">
  <img alt="Estilo CATEGORY" class="w-full h-full object-cover rounded-xl group-hover:scale-110 transition-transform duration-700" src="data:image/jpeg;base64,..."/>
  <div class="absolute inset-1.5 rounded-xl bg-gradient-to-t from-black/70 via-transparent to-transparent pointer-events-none"></div>
  <div class="absolute bottom-4 left-4 f-body text-[10px] uppercase tracking-[.16em] text-white/85">CATEGORY</div>
</div>
```
All items ship with the `hidden` class except the ones in the default-active
category (currently Love); the chip-click handler toggles it.

### Carousel (`#stage`)

Hero image carousel, driven by a JS array literal `const SLIDES = [...]` (search
for it near the bottom of the `<script>` block — do NOT confuse with the
lowercase `slides` variable name, it's `SLIDES` uppercase). Each entry:
```js
{ src:"data:image/jpeg;base64,...", eyebrow:"CategoryName", label:"Display Title" }
```
`active = 0` on load, so **whichever entry is first in the array is what's
shown first** — order matters, this has been used deliberately to control
which photo opens the page.

Current curated selection (7 slides, hand-picked "best of" across categories,
intentionally NOT one-per-category — Love is over-represented as the flagship
style):

1. Love — "Latidos de amor"
2. Minimal white — "Instante puro"
3. Minimal black — "Bajo la luz"
4. Love — "Alegría infinita"
5. Minimal white — "Mirada curiosa"
6. Love — "Pequeños destellos"
7. Minimal black — "Foco de ternura"

Fantasía and Estudio were deliberately removed from the carousel (kept only in
the styles gallery) at Alba's request. When curating carousel slides, prefer
reusing an already-embedded base64 string from the `#estilos` grid (extract via
regex) rather than re-encoding the source photo a second time — keeps file size
down and guarantees the carousel and gallery show pixel-identical images.

### Pricing (`#pricing` + `#pricing-print`)

**Packs digitales** (`#pricing`), 3 cards:
| Card | Price | Notes |
|---|---|---|
| Basic | 9,90€ | 5 retratos, 1 estilo, imágenes solo del bebé |
| Flex | 14,90€ | "Más popular" badge. 15 retratos, todos los estilos disponibles, imágenes solo del bebé |
| Regala un pack | "€ según selección" | Digital gift code, redeemable for any digital pack, 1-year validity. Button → `proximamente.html?producto=regalo-digital` |

**Packs impresos** (`#pricing-print`), 3 cards:
| Card | Price | Notes |
|---|---|---|
| Álbum o póster | 29,90€ | 15 retratos máx. resolución, impresión 13×13cm, envío incluido, todos los estilos, solo fotos del bebé. Button → `proximamente.html?producto=album-poster` |
| Pack de imanes | 39,90€ | "Novedad" badge. 15 imanes cuadrados, envío incluido, todos los estilos, solo fotos del bebé. Button → `proximamente.html?producto=imanes` |
| Regala un pack | "€ según selección" | Print gift code, 1-year validity. Button → `proximamente.html?producto=regalo-impreso` |

The **printed packs and both gift-card options are not part of the live MVP
yet** — their buttons link out to `proximamente.html` (waitlist) instead of an
actual checkout. Only Basic and Flex are "real" purchasable buttons in the
current build (they currently don't link anywhere either — no checkout/payment
integration exists yet at all; that's a known gap, not a bug).

### Copy consistency rules (learned the hard way — check before touching timing claims)

Delivery time is **24–48h**, not instant/same-day. This appears in four
places that must stay consistent — if one changes, check the other three:
1. Step 3 of "Cómo funciona" ("Enamórate del resultado")
2. "Sin Esperas" benefit card
3. FAQ "¿Cuánto tarda la entrega?"
4. `pedido.html` step 4 confirmation copy

## Page 2: `proximamente.html`

Standalone "coming soon" waitlist page, visually matched to the main site
(same fonts, same dark/purple glass aesthetic, same `.reveal` animation
pattern) but self-contained — it does not `@import` or share code with
`petit_studio_v3.html`, it's a fully independent copy of the relevant tokens.
Signature visual element: a pulsing heart-outline SVG (ties back to the Love
style / brand identity).

Linked from 4 buttons in `petit_studio_v3.html` via query string `?producto=X`:

| `producto` value | Displayed label |
|---|---|
| `regalo-digital` | Regalo digital |
| `album-poster` | Fotos |
| `imanes` | Imanes |
| `regalo-impreso` | Regalo impreso |

Label mapping lives in a `PRODUCTS` object near the bottom of the page's
`<script>` block — edit there to rename labels or add new product keys.
Falls back to "Esta opción" if the query param is missing/unrecognized.

Form: Nombre, Apellidos, Email → on submit:
1. Saves an entry to `localStorage['petitstudio_interesados']` (JSON array) —
   per-browser local log only, kept purely as a lightweight backup.
2. POSTs the structured lead (`nombre`, `apellidos`, `email`, `producto`,
   `producto_label`, `fecha`, `hora`) as JSON to a **Formspree** endpoint
   (`FORMSPREE_ENDPOINT` constant near the bottom of the `<script>` block) —
   this is the real, persistent, structured store. Each submission lands as a
   row in the Formspree dashboard (one column per field) and triggers
   Formspree's own email notification to Alba automatically.
3. Only if that request fails (endpoint not configured yet, offline, etc.)
   does it fall back to opening a `mailto:petitstudio@gmail.com` link
   pre-filled with the same data, as a safety net so the lead isn't lost.
4. Swaps the form out for a confirmation state (`#formState` → `#successState`)
   either way.

#### Formspree setup

`FORMSPREE_ENDPOINT` in `proximamente.html` is live: `https://formspree.io/f/myegkbqq`
(Alba's real form — configured). Submissions land in that form's Formspree
dashboard as structured rows and trigger Formspree's notification email.
If it's ever replaced (new account, new form), just swap the URL in the
`FORMSPREE_ENDPOINT` constant — no other code changes needed. Worth
double-checking in the Formspree dashboard that the destination email
(petitstudio@gmail.com) is confirmed, or notification emails get blocked.

### Linked buttons → producto values

Only the buttons that already point at `proximamente.html` feed the lead
capture above: `regalo-digital`, `album-poster`, `imanes`, `regalo-impreso`
(see Pricing table below). **Basic and Flex intentionally remain unlinked** —
per Alba's decision, they stay a known gap (no checkout yet) rather than
being routed into the waitlist/lead-capture flow. Don't link them without
checking with her first.

### Known limitation — flagged to Alba, not yet resolved

This is still a static HTML file with **no custom backend** — Formspree is a
third-party no-code form endpoint, not a database Alba controls directly. If
she outgrows the free tier or wants full control/export (e.g. into a real
database, CRM, or Google Sheet), good next steps: Formspree's paid tiers add
Google Sheets sync and higher volume; alternatively **Firebase Firestore**
(free Spark tier) or a small serverless function (Vercel/Cloudflare Workers)
if she wants full control — both would need her to create the
project/credentials herself (requires her Google/cloud account), so revisit
only if she explicitly asks. Don't build a custom backend unless she
explicitly asks for one — start with the no-code options.

## Page 3: `pedido.html` — order wizard (Phase 1, in progress)

4-step wizard for placing an order — what the Basic (`?pack=basic`) and Flex
(`?pack=flex`) "Seleccionar" buttons on `petit_studio_v3.html` link to.
Steps: Fotos → Estilos → Datos → Listo. All state (`state` object in the
`<script>`) lives in memory for the session; nothing is persisted or sent
anywhere yet.

**Phase 1 status: frontend only. Payment and generation are mocked.**
See "Roadmap" below for what's still needed.

### ⚠️ `pedido.html` is GENERATED — never edit it directly

```
pedido.template.html  ← EDIT THIS (the real source, ~35 KB, readable)
build_pedido.py       ← run this to regenerate
pedido.html           ← OUTPUT, ~6 MB, git-tracked because Vercel serves it
```

`build_pedido.py` extracts the 43 catalog photos (category + alt + base64
`src`) from `petit_studio_v3.html`'s `#estilos` gallery and injects them into
the template's `__CATALOG_JSON__` placeholder. So the wizard and the main site
always show pixel-identical images, and no photo is ever encoded twice.

After **any** change to `pedido.template.html`, or to the `#estilos` gallery in
`petit_studio_v3.html`, run:

```
python3 build_pedido.py
```

It sanity-checks that the number of extracted items matches the number of
`gallery-item`s in the source and fails loudly if the regex has drifted from
the markup.

`.vercelignore` keeps the template, the build script and this file out of the
deployment — only the generated `pedido.html` ships.

### Layout & responsive

Mobile-first, verified at 375 / 768 / 1280 px with no horizontal overflow.
**Critical layout lives in the page's own `<style>` block, not in Tailwind
classes** (`.wrap`, `.thumb-grid`, `.style-grid`, `.chips-row`, `.stepper`,
`.btn`…). Tailwind arrives over CDN, and a slow or blocked CDN would otherwise
leave the page with no grid and browser-default button styling — which also
silently broke colour contrast the first time round. Tailwind is still loaded
and used for spacing/typography utilities; just don't put structural layout or
anything contrast-critical in a Tailwind-only class.

Grid columns: thumbnails 3 / 4 / 5, style cards 2 / 3 / 4 (mobile / ≥640 / ≥1024).

### Chrome that stays on screen

Three persistent regions, all sticky — the client never has to scroll to know
where they stand:

| Region | Where | Contains |
|---|---|---|
| `.app-header` | sticky top | back arrow (icon only — no "Petit Studio" wordmark) + stepper |

The stepper stacks each numbered dot with its name underneath, and **all three
names stay visible at every width**, down to 320px — not just the active one.
Items align to the top and `.step-sep` is pushed down 13px (half a dot) so the
connecting lines sit at dot height. The header's own flex layout lives in
`.app-header-inner`, not in Tailwind classes, for the same CDN reason as the
rest of the critical layout.
| `#contextBar` | sticky, directly under the header (its `top` is set from the header's measured height on load/resize) | steps 1–2 only: the live counter |
| `.action-bar` | sticky bottom, `env(safe-area-inset-bottom)`-aware | Atrás (ghost, left) + primary CTA (right; full-width on mobile) |

The header back arrow is shown on steps 1–3 and hidden on the final screen
(the order is already placed; that screen has its own "Volver a Petit Studio"
link). **On step 1 it leaves the flow entirely** and returns to
`petit_studio_v3.html` — if any photos have been added it confirms first, since
nothing is persisted yet and leaving discards them. From step 2 onwards it just
goes back one step. Its `aria-label` changes accordingly. The bottom bar's
"Atrás" stays hidden on step 1 so the primary CTA keeps the full width.

The **counter is at the top, not the bottom** — Alba's explicit requirement:
while picking photos or styles it must be visible without scrolling to the end.
It is also deliberately **short (~41px)**: one line of text plus a 4px bar, so
it rides along with the scroll without stealing height from the content. The
tier tip and selection hint that change as you go are *not* in that bar — they
live in the step body (`#meterTip`, `#selHint`) precisely to keep it thin. If
you add anything to the context bar, keep it to one line.

Every selection/removal also fires a toast (`toast()`, `#toastRegion`,
`role="status"`) with the running total, so feedback is immediate.

### Three steps, then a final screen

`STEPS` has **three** entries (Fotos, Estilos, Datos) and the step-3 CTA reads
**"Confirmar"**. The confirmation screen is `DONE_STEP` (4) — internally still
`#step4`, but it is *not* a step: the stepper (`#stepperNav`) and the action bar
are both hidden there. Don't reintroduce a "Paso X de Y" line inside any step
either — the stepper already says it, and Alba had it removed as redundant.

### Step 1 — Fotos

Title "Sube sus fotos", subtitle "3 fotos mínimo, con 5 capturamos los matices
de ternura." Drag-and-drop or file picker, 3–10 photos, read client-side as data
URLs (nothing is uploaded in Phase 1). Quality meter (`TIERS`) reacts to photo
count with label + emoji + colour + bar, and a matching tip below the dropzone:

| Fotos | Etiqueta | Color |
|---|---|---|
| 0–2 | "Añade 3 fotos para empezar" 🌱 | rojo |
| 3–4 | "Suficiente para empezar" 🙂 | naranja |
| 5–7 | "Muy buen material" 😊 | ámbar |
| 8–10 | "Perfecto, así da gusto" 🤩 | verde |

Colour is never the only signal (label + emoji + text carry it too) — WCAG 1.4.1.

### Step 2 — Estilos

Catalog cards are real `<button aria-pressed>` elements (keyboard-operable,
announced as pressed/not pressed). Category chips are `<button aria-pressed>`
too.

Pack limits (`PACKS`):
- **Basic** — `singleCategory: true`, max 5. The first pick sets
  `state.lockedCategory`.
- **Flex** — max 15, any mix of categories.

**The client must fill the pack completely to continue** — 5 of 5, 15 of 15.
A partial selection keeps the CTA blocked and explains what's missing.

**`PACKS` is the single source of truth — adding a pack must not require
touching the flow.** Its `max`, `label` and `singleCategory` drive the
counters, hints, validation, toasts and step-2 subtitle; `?pack=` accepts any
key in `PACKS` and falls back to the first one. Never hardcode a pack's name or
size anywhere else (this was already wrong once: the step-2 subtitle said "Pack
Flex" for every non-Basic pack). To add "premium", add one entry to `PACKS` —
nothing else.

**The Basic lock lives on the chips, not on the cards.** Once a style is
locked, every other chip gets `aria-disabled`, a lock icon and an explanatory
`aria-label`; clicking one shows a toast and does *not* switch category. Alba
asked for this explicitly: previously you could browse into another style and
only find out it was blocked by clicking a photo. Because the chips are the
only way into another category, a card can never be un-selectable — so there is
no "locked card" state, and `toggleSelect` only has to guard the max count.
Removing every selection clears the lock and re-enables the chips.

**Selecting does NOT re-render the grid.** `toggleSelect()` updates only the
clicked card's `aria-pressed`, then `renderChips()` + the counter. Rebuilding
the grid (as the first version did) threw away keyboard focus and scroll
position on every click — don't reintroduce that.

### Step 3 — Datos

**Labels sit above the inputs** (`.field-label`), always visible. The fields
keep the site's original input styling (14/16px padding, 14px radius, `.95rem`,
52px min-height). Do not go back to placeholder-as-label — the label vanished
as soon as you typed — and do not switch to a floating label either: Alba
asked for the original input look with a proper label above it.

⚠️ **The field selectors are `input.field` / `input.checkbox-input`, not
`.field` / `.checkbox-input` — keep them that way.** Tailwind's `forms` plugin
styles fields via `[type='text']`, which has the *same* specificity (0,1,0) as
a class, and the CDN injects its stylesheet **after** the page's `<style>`
block, so it won. In production that meant white boxes with white text —
completely invisible — square corners, and a Tailwind-blue checkbox; locally it
looked fine because the CDN is unreachable, so the bug only ever showed up on
the deployed site. Anything targeting a form control needs the element
qualifier (or has to beat `[type=…]` some other way). The checkbox is fully
custom (`appearance:none` + a `clip-path` tick) for the same reason —
`accent-color` does nothing once the plugin sets `appearance:none`. There is
also a `:-webkit-autofill` override, since Chrome otherwise repaints the field
with its own light background.

When testing this file locally, remember the sandbox has no CDN access: to
catch this class of bug, inject the `forms` plugin's base CSS into the page
after load and re-check computed styles and contrast.

Inline validation: `aria-invalid` + `hidden` error nodes wired via
`aria-describedby`, first invalid field gets focus, errors clear as the user
types.

Gate copy across the flow (the CTA is `aria-disabled`, so pressing it always
explains itself rather than doing nothing): step 1 blocks below 3 photos with
"Añade mínimo 3 fotos para continuar."; step 2 blocks until the pack is full
with "Elige las N fotos de tu pack para continuar. Te faltan X.". Consent checkbox is **required and unchecked by default**, with
inclusive wording ("madre, padre o tutor/a legal de la criatura") — do not
reword to gendered-only, do not pre-check (legal requirement, photos of a
minor).

The summary card shows only the pack, its price and the number of chosen
photos. It deliberately does **not** show the uploaded-photo count, and has no
"change my pack/selection" link: switching pack changes the whole flow
(different limits, possibly an already-locked style), so it is not offered here
— going back through the stepper or the back arrow is the way.

Payment is simulated (1.1s delay); the `TODO Fase 2` comment marks where the
Stripe Checkout redirect goes.

### Final screen — Confirmación

Heart-pulse SVG, mock reference `PS-<timestamp>`, and the 24–48h promise (see
Copy consistency rules — this is the 4th place it appears). Stepper and action
bar are hidden; the only action is "Volver a Petit Studio".

⚠️ The copy tells the client **"Te hemos enviado a {email} un correo con la
confirmación de tu pedido"** — and in Phase 1 no such email is sent, because
there is no backend. Alba asked for this wording; it is a promise that Phase 2
has to make true. The confirmation email is part of roadmap item 5, and it must
ship together with (or before) real payments — a client who pays and never gets
the confirmation the screen promised is a support problem.

### Accessibility — verified, keep it that way

Audited with **axe-core (WCAG 2.1 A + AA) across all four steps, including
error and selection states: 0 violations.** Re-run after any change to the
template (serve the folder, then drive it with Playwright + axe).

What's load-bearing — don't undo:
- `[hidden]{ display:none !important; }` — without it `.btn`/`.icon-btn`'s
  `display` wins over the `hidden` attribute and "hidden" buttons stay in the
  tab order. This was a real bug.
- `:focus-visible` outline (3px, `#c4a6ff`) — never `outline:none` on inputs.
- Primary CTA uses `aria-disabled` + an explanatory toast on click, **not**
  `disabled` — a `disabled` button is unreachable by keyboard and tells a
  screen-reader user nothing about what's missing.
- All body text ≥ `rgba(255,255,255,.64)` on `#050508` (`.t-primary` /
  `.t-secondary` / `.t-muted`). Below that, contrast fails AA.
- Touch targets ≥ 44×44 (`.btn`, `.icon-btn`, `.chip`, `.thumb-remove`).
  The `sr-only` file input is the one exception — its `<label>` is the target.
- `role="status"` toast region, `role="progressbar"` + `aria-valuetext` on both
  meters, `aria-current="step"` on the active step, heading focus on step
  change, skip link, `prefers-reduced-motion` block.

### Roadmap (Phase 2+, not started — needs Alba's accounts/credentials)

Discussed with Alba; don't build ahead of her go-ahead on each piece:
1. **Storage + database** — photos and orders need to persist (survive reloads,
   allow regeneration, feed the 360 reference grid). Recommended: Supabase
   (Postgres + Storage + Auth, generous free tier). Needs her account.
2. **Real payment** — replace the mocked submit with a Stripe Checkout session
   created by a Vercel serverless function. Needs her Stripe account.
3. **Image generation** — send photos + style prompts to Google's Gemini API:
   (a) build a "360 reference grid" of the baby's face/angles to keep identity
   consistent across styles, (b) generate one image per selected style from
   that reference + the style's prompt (prompt library lives outside this repo).
   Needs a Google AI API key.
4. **Admin review dashboard** — private, authenticated panel listing orders,
   prompts sent, generation status and results, with approve / regenerate /
   replace actions. Notify Alba when a batch finishes.
5. **Delivery email** — on approval, email the client a secure expiring
   download link (Resend or similar; Formspree is only wired to
   `proximamente.html` leads). These are photos of a minor: prefer short link
   expiry + automatic deletion after delivery over indefinite retention.

## Editing conventions used throughout this project

- Prefer scripted `re.sub` / `str.replace` on unique anchor text (an `alt=`
  attribute, a `data-category`, a distinctive class combo) over hand-editing —
  the file is too large and base64-heavy to safely eyeball diffs.
- When removing/reordering carousel slides or gallery items, always re-verify
  counts afterward (`grep -c 'data-category="X"'`, count `SLIDES` entries) —
  it's easy to silently under/over-match with regex on a file this repetitive.
- Never duplicate an already-embedded photo — if a requested photo turns out
  to be byte-identical (or the literal same source file) to one already on the
  site, reuse the existing base64 string instead of re-encoding it.
- This CLAUDE.md should be kept in sync manually — there's no automation that
  updates it. After a significant structural change (new category, new
  section, pricing change, new linked page), update the relevant table above
  in the same session.

## Style catalog context (broader business, not encoded in this repo)

The website only surfaces a subset of Alba's prompt-engineering catalog for
the AI portrait generator (Minimal, Dreamy/Fantasía, Wrapped, Black & White
Fine Art, Painting, Seasonal, Professions, Digital Neon Art, and the flagship
LOVE heart-relief series). That prompt library itself lives outside this
website project (it's a separate body of work — structured prompts per style,
per color variant, with a pose repertoire and quality-control checklist) and
isn't part of this codebase. If asked to add a new *style category* to the
site, that's a website task (new chip + gallery items, following the patterns
above); if asked to *design a new AI-generation prompt*, that's a different
kind of work this file doesn't cover.
