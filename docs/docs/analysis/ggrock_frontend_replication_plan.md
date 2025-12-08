# ggRock Frontend Replication Plan

## Pregled

Plan za analizu i replikaciju ggrock frontend build-a (`ggRockPocUi`) u React aplikaciju za ggnet2.

## Faza 1: Analiza ggrock Build-a

### 1.1 Lokacija Build-a
- **Standardna lokacija**: `/opt/ggrock/app/ggRockPocUi/`
- **Alternativna lokacija**: Može biti u bilo kom direktorijumu gde je instaliran ggrock

### 1.2 Struktura Build-a
Očekivana struktura:
```
ggRockPocUi/
├── index.html          # Main HTML file
├── assets/             # Static assets
│   ├── css/           # Stylesheets
│   ├── js/            # JavaScript files
│   └── images/        # Images
├── static/            # Static files
└── ...                # Other files
```

### 1.3 Analiza Fajlova

#### HTML Analiza
- **index.html**: Glavni HTML fajl
  - Struktura stranice
  - Navigation
  - Main content areas
  - Script tags (React, Vue, Angular, ili vanilla JS)
  - CSS links

#### JavaScript Analiza
- **Framework**: Identifikacija framework-a (React, Vue, Angular, ili vanilla JS)
- **Routing**: Kako se rukuje rutiranjem
- **API Calls**: Kako se pozivaju API endpoint-i
- **State Management**: Kako se rukuje stanjem
- **Components**: Struktura komponenti

#### CSS Analiza
- **Design System**: Boje, tipografija, spacing
- **Layout**: Grid, flexbox, ili custom layout
- **Components**: Button, card, table, modal, itd.
- **Responsive**: Mobile/tablet/desktop breakpoints

### 1.4 Funkcionalnosti

#### Stranice/Views
- Dashboard
- Images management
- Machines management
- VMs management
- Storage management
- Network configuration
- Settings
- Client management

#### Komponente
- Navigation/Sidebar
- Data tables
- Forms
- Modals
- Charts/Graphs
- Status indicators
- Action buttons

## Faza 2: Rekonstrukcija Strukture

### 2.1 Komponente Mape
```
app/frontend/src/
├── components/
│   ├── Layout/          # Main layout
│   ├── Navigation/      # Sidebar/Navbar
│   ├── DataTable/       # Reusable table
│   ├── Form/            # Reusable form
│   ├── Modal/           # Modal dialog
│   ├── Card/            # Card component
│   ├── Button/          # Button component
│   ├── StatusBadge/     # Status indicator
│   └── Chart/           # Chart component
├── pages/
│   ├── Dashboard/
│   ├── Images/
│   ├── Machines/
│   ├── VMs/
│   ├── Storage/
│   ├── Network/
│   ├── Settings/
│   └── Clients/
└── styles/
    ├── variables.css    # CSS variables (colors, spacing)
    ├── base.css         # Base styles
    └── components.css   # Component styles
```

### 2.2 Design System
- **Colors**: Primary, secondary, success, error, warning, info
- **Typography**: Font families, sizes, weights
- **Spacing**: Margin, padding scale
- **Shadows**: Elevation levels
- **Borders**: Border radius, widths

## Faza 3: Implementacija

### 3.1 Komponente
1. **Layout Component**
   - Sidebar navigation
   - Main content area
   - Header/Topbar
   - Footer (optional)

2. **Navigation Component**
   - Menu items
   - Active state
   - Icons
   - Collapsible sections

3. **Data Table Component**
   - Sorting
   - Filtering
   - Pagination
   - Row actions
   - Selection

4. **Form Components**
   - Input fields
   - Select dropdowns
   - Checkboxes/Radio buttons
   - Date pickers
   - File uploads

5. **Modal Component**
   - Open/close
   - Backdrop
   - Animations
   - Form modals
   - Confirmation dialogs

6. **Status Components**
   - Badges
   - Icons
   - Progress bars
   - Loading states

### 3.2 Stranice
1. **Dashboard**
   - Statistics cards
   - Charts/Graphs
   - Recent activity
   - Quick actions

2. **Images**
   - Image list table
   - Create/Edit image
   - Image details
   - Snapshot management

3. **Machines**
   - Machine list table
   - Machine details
   - Boot configuration
   - Status monitoring

4. **VMs**
   - VM list table
   - VM details
   - VM console (VNC)
   - VM actions (start/stop/reset)

5. **Storage**
   - Pool status
   - Dataset list
   - ARC statistics
   - IO statistics

6. **Network**
   - Network configuration
   - iPXE boot setup
   - iSCSI targets
   - DNS configuration

7. **Settings**
   - Settings list
   - Create/Edit setting
   - Bulk update
   - Categories

8. **Clients**
   - Client list
   - Client details
   - Client status
   - Real-time updates

## Faza 4: Stilizacija

### 4.1 CSS Variables
```css
:root {
  /* Colors */
  --color-primary: #...;
  --color-secondary: #...;
  --color-success: #...;
  --color-error: #...;
  --color-warning: #...;
  --color-info: #...;
  
  /* Typography */
  --font-family: '...', sans-serif;
  --font-size-base: 14px;
  --font-size-lg: 16px;
  --font-size-sm: 12px;
  
  /* Spacing */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
  
  /* Borders */
  --border-radius: 4px;
  --border-width: 1px;
}
```

### 4.2 Komponente Stilovi
- Consistent spacing
- Consistent colors
- Consistent typography
- Consistent shadows
- Consistent borders

## Faza 5: Funkcionalnosti

### 5.1 API Integracija
- Sve API pozive kroz service layer
- Error handling
- Loading states
- Success/Error notifications

### 5.2 Real-time Updates
- WebSocket connection
- Live status updates
- Live data refresh

### 5.3 User Experience
- Loading indicators
- Error messages
- Success messages
- Confirmation dialogs
- Form validation

## Koraci za Implementaciju

### Korak 1: Dobijanje Build-a
1. Pronaći ggrock build (`/opt/ggrock/app/ggRockPocUi/` ili druga lokacija)
2. Kopirati build u projekat (opciono, za analizu)
3. Kreirati `docs/analysis/ggrock_frontend/` direktorijum

### Korak 2: Analiza
1. Analizirati `index.html`
2. Analizirati JavaScript fajlove
3. Analizirati CSS fajlove
4. Dokumentovati strukturu i funkcionalnosti

### Korak 3: Planiranje
1. Identifikovati komponente
2. Identifikovati stranice
3. Identifikovati funkcionalnosti
4. Kreirati task listu

### Korak 4: Implementacija
1. Kreirati komponente
2. Implementirati stranice
3. Stilizovati UI
4. Integrisati API

### Korak 5: Testiranje
1. Testirati funkcionalnosti
2. Testirati UI/UX
3. Testirati responsive design
4. Testirati API integraciju

## Napomene

- **Framework**: ggrock frontend može biti u React-u, Vue-u, Angular-u, ili vanilla JavaScript-u
- **Build Tools**: Može koristiti Vite, Webpack, ili druge build tools
- **State Management**: Može koristiti Redux, Zustand, Vuex, ili druge
- **Styling**: Može koristiti CSS, SCSS, Tailwind, ili druge

## Sledeći Koraci

1. **Dobijanje Build-a**: Pronaći ggrock build i kopirati ga u projekat
2. **Analiza**: Analizirati strukturu i funkcionalnosti
3. **Dokumentacija**: Dokumentovati nalaze
4. **Planiranje**: Kreirati detaljan plan implementacije
5. **Implementacija**: Početi sa implementacijom

