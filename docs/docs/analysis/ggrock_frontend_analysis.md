# ggRock Frontend Analysis

## Pregled

Analiza ggrock frontend build-a (`ggRockPocUi`) iz paketa `ggrock_0.1.2200.2324-1_amd64`.

## Framework Identifikacija

**Framework**: Angular
- **Indikator**: `<app-root></app-root>` tag u HTML-u
- **Build Tool**: Angular CLI (verovatno)
- **Module System**: ES Modules (`type="module"`)

## Struktura Build-a

```
ggRockPocUi/default/
├── index.html              # Main HTML file
├── runtime.bf691d7b3ea8cc80.js
├── polyfills.f0b4e0069aa14095.js
├── main.3b0cf76ac7a3e98f.js
├── styles.cfcd9934c3b89096.css
├── common.6f5c35b3f4624699.js
├── [chunk].js              # Multiple chunk files
├── assets/
│   ├── favicon.png
│   ├── fonts/
│   ├── gg-account/
│   ├── gg-employees/
│   ├── gg-profile/
│   ├── gg-shared/
│   ├── images/
│   └── json/
└── [font files]
```

## Design System

### CSS Variables

```css
:root {
  /* Colors */
  --ds__ui_text_high-emphasis: rgba(255, 255, 255, .88);
  --ds__ui_text_medium-emphasis: rgba(255, 255, 255, .64);
  --ds__ui_text_low-emphasis: rgba(255, 255, 255, .32);
  
  /* Backgrounds */
  --ds__ui_background_01: #171a1c;
  --ds__ui_background_02: #2e3438;
  --ds__ui_background_03: #454e54;
  
  /* Surfaces */
  --ds__ui_surface_enabled: rgba(255, 255, 255, .06);
  --ds__ui_surface_hover: rgba(255, 255, 255, .12);
  --ds__ui_surface_focus-pressed: rgba(255, 255, 255, .16);
  --ds__ui_surface_selected: rgba(97, 162, 209, .16);
  --ds__ui_surface_activated: rgba(97, 162, 209, .24);
  
  /* Interactive */
  --ds__ui_interactive_enabled: #61a2d1;
  --ds__ui_interactive_hover: #88b9dd;
  --ds__ui_interactive_press: #b0d1e8;
  --ds__ui_accent: #61a2d1;
  
  /* Alerts */
  --ds__ui_alert_success: #7ab889;
  --ds__ui_alert_warning: #fba337;
  --ds__ui_alert_error: #d65e5c;
  
  /* Metallic Gradients */
  --ds__ui_metallic_gold: linear-gradient(120.81deg, #bc841f 8.1%, #f9c66c 93.02%);
  --ds__ui_metallic_silver: linear-gradient(116.01deg, #a0a5c5 7.9%, #cfe0e2 91.11%);
  --ds__ui_metallic_bronze: linear-gradient(116.01deg, #874a12 9.48%, #d3975f 92.69%);
  
  /* Border Radius */
  --ds__border_radius_xxs: 2px;
  --ds__border_radius_xs: 4px;
  --ds__border_radius_s: 8px;
  --ds__border_radius_m: 12px;
  --ds__border_radius_l: 16px;
  --ds__border_radius_xl: 24px;
  --ds__border_radius_xxl: 32px;
  
  /* Shadows */
  --ds__ui_drop_shadow: 0px 2px 8px rgba(0, 0, 0, .64);
  --ds__ui_drop_shadow_02: 0px 4px 24px rgba(0, 0, 0, .48);
  --ds__ui_drop_shadow_03: 0px 16px 48px rgba(0, 0, 0, .32);
  
  /* Backdrop Filters */
  --ds__ui_backdrop_filter: blur(74px);
  --ds__ui_backdrop_filter_02: blur(48px);
  --ds__ui_backdrop_filter_03: blur(32px);
  --ds__ui_backdrop_filter_04: blur(16px);
  
  /* Typography */
  --ds__font-family: "Inter", sans-serif;
  --ds__disabled-opacity: .32;
  
  /* Layout */
  --header-block-height: 56px;
  --content-header-height: 64px;
  --form-horizontal-padding: 1.5em;
}
```

### Color Palette

**Primary Colors:**
- Background 01: `#171a1c` (Dark)
- Background 02: `#2e3438` (Medium Dark)
- Background 03: `#454e54` (Light Dark)

**Accent Colors:**
- Primary: `#61a2d1` (Blue)
- Hover: `#88b9dd` (Light Blue)
- Press: `#b0d1e8` (Lighter Blue)
- EGL Accent: `#fed130` (Yellow)

**Alert Colors:**
- Success: `#7ab889` (Green)
- Warning: `#fba337` (Orange)
- Error: `#d65e5c` (Red)

**Metallic Gradients:**
- Gold: `linear-gradient(120.81deg, #bc841f 8.1%, #f9c66c 93.02%)`
- Silver: `linear-gradient(116.01deg, #a0a5c5 7.9%, #cfe0e2 91.11%)`
- Bronze: `linear-gradient(116.01deg, #874a12 9.48%, #d3975f 92.69%)`

### Typography

**Font Families:**
- Primary: `"Inter", sans-serif`
- Roboto (Google Fonts)
- Material Icons
- Overpass
- Overpass Mono
- Brandon Grotesque (custom fonts)

**Font Weights:**
- 300 (Light)
- 400 (Regular)
- 500 (Medium)
- 600 (Semi-Bold)
- 700 (Bold)
- 800 (Extra Bold)

### Spacing

- Form horizontal padding: `1.5em`
- Header block height: `56px`
- Content header height: `64px`

### Shadows

- Drop shadow: `0px 2px 8px rgba(0, 0, 0, .64)`
- Drop shadow 02: `0px 4px 24px rgba(0, 0, 0, .48)`
- Drop shadow 03: `0px 16px 48px rgba(0, 0, 0, .32)`

### Border Radius

- XXS: `2px`
- XS: `4px`
- S: `8px`
- M: `12px`
- L: `16px`
- XL: `24px`
- XXL: `32px`

## Assets

### Images
- `assets/images/ggrock-logo.svg`
- `assets/images/header-logo.svg`
- `assets/images/new-ggrock-logo.svg`
- `assets/images/icons/` (various icons)
- `assets/images/auth/bg-blue-gradient.jpg`

### Fonts
- Brandon Grotesque (Bold, Black)
- Helvetica
- Custom font files in `assets/fonts/`

### JSON Data
- `assets/json/arrays.json`
- `assets/json/disks-images.json`
- `assets/json/images.json`
- `assets/json/machines.json`
- `assets/json/stats.json`
- `assets/json/writebacks.json`
- `assets/json/updates.json`
- `assets/json/stripe-items.json`
- `assets/json/dhcp-settings.json`
- `assets/json/image-settings.json`
- `assets/json/backup-restore-images.json`
- `assets/json/validate-array.json`
- `assets/json/empty-array.json`
- `assets/json/free-drives.json`

### i18n (Internationalization)
- Multiple language support
- Languages: `en`, `ru`, `pt-BR`, `pt`, `tr`, `lt`, `es`, `fr`, `it`, `id`, `et`, `bg`, `ar`, `cn`, `de`
- Translation files in `assets/gg-shared/i18n/`, `assets/gg-account/i18n/`, `assets/gg-employees/i18n/`, `assets/gg-profile/i18n/`

## External Dependencies

### Scripts
- Chat widget: `https://cdn.chat.appfire.app/app/widget-prod/get-chat.min.js`
- Chat helpers: `https://media.ggleap.com/gg-chat-widget-helpers.js`
- Stripe Checkout: `https://checkout.stripe.com/checkout.js`
- Stripe JS: `https://js.stripe.com/v3/`

### Fonts
- Google Fonts: Roboto, Material Icons, Overpass, Overpass Mono

## Theme

**Theme Type**: Dark Theme
- Background: `#171a1c` (Very dark gray)
- Text: White with varying opacity
- Accent: Blue (`#61a2d1`)

## Layout

- **Min Width**: `768px`
- **Height**: `100%`
- **Overflow**: `overflow-x: auto; overflow-y: hidden`

## Komponente (iz JSON fajlova)

Na osnovu JSON fajlova, mogu se identifikovati sledeće komponente:

1. **Arrays** - Array management
2. **Disks/Images** - Disk and image management
3. **Images** - Image management
4. **Machines** - Machine management
5. **Stats** - Statistics
6. **Writebacks** - Writeback management
7. **Updates** - Update management
8. **Stripe Items** - Payment integration
9. **DHCP Settings** - Network configuration
10. **Image Settings** - Image configuration
11. **Backup/Restore Images** - Backup management
12. **Validate Array** - Array validation
13. **Free Drives** - Drive management

## Sledeći Koraci za Replikaciju

1. **Kreirati React komponente** sa istim dizajnom
2. **Implementirati CSS varijable** za design system
3. **Kreirati komponente** za sve stranice
4. **Implementirati dark theme**
5. **Dodati i18n podršku** (opciono)
6. **Kreirati reusable komponente** (Button, Card, Table, Modal, itd.)

