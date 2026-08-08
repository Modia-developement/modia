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
- Redeploy after changes with `npx vercel --prod --yes` from inside
  `petit-studio-project/` (requires being logged into the `modia.developement`
  Vercel account — `npx vercel whoami` to check, `npx vercel login` to switch).
- No custom domain connected yet — the `.vercel.app` URL is what's live.

## Files

```
petit_studio_v3.html   ← main site (single file, self-contained, offline-capable)
proximamente.html      ← "coming soon" waitlist page for features not yet live
vercel.json             ← rewrite so "/" serves petit_studio_v3.html on Vercel
CLAUDE.md              ← this file
```

There is **no build step, no framework, no package.json**. Both pages are raw
HTML + Tailwind (via CDN `<script>`) + vanilla JS in inline `<script>` tags.
Open either file directly in a browser — nothing needs to be served or compiled.

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

Delivery time is **24–48h**, not instant/same-day. This appears in three
places that must stay consistent — if one changes, check the other two:
1. Step 3 of "Cómo funciona" ("Enamórate del resultado")
2. "Sin Esperas" benefit card
3. FAQ "¿Cuánto tarda la entrega?"

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
