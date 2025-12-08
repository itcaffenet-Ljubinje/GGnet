# ggRock Frontend Replication Plan

## Pregled

Plan za replikaciju ggrock frontend-a u React aplikaciju za ggnet2.

## Analiza

### Framework
- **ggrock**: Angular
- **ggnet2**: React (Vite)

### Design System
- **Theme**: Dark theme
- **Primary Color**: `#61a2d1` (Blue)
- **Background**: `#171a1c` (Very dark gray)
- **Typography**: Inter/Roboto

## Faza 1: Design System ✅

- [x] Analizirati ggrock CSS varijable
- [x] Kreirati design-system.css sa svim varijablama
- [x] Uključiti design system u index.css

## Faza 2: Base Components

### 2.1 Button Component
- [ ] Kreirati Button komponentu
- [ ] Varijante: primary, secondary, success, error, warning
- [ ] States: enabled, hover, pressed, disabled
- [ ] Sizes: small, medium, large

### 2.2 Card Component
- [ ] Kreirati Card komponentu
- [ ] Varijante: default, elevated, outlined
- [ ] Header, body, footer sekcije

### 2.3 Table Component
- [ ] Kreirati Table komponentu
- [ ] Sorting, filtering, pagination
- [ ] Row selection
- [ ] Actions column

### 2.4 Modal Component
- [ ] Kreirati Modal komponentu
- [ ] Backdrop blur
- [ ] Animations
- [ ] Form modals
- [ ] Confirmation dialogs

### 2.5 Status Badge Component
- [ ] Kreirati StatusBadge komponentu
- [ ] Varijante: success, warning, error, info
- [ ] Icons support

### 2.6 Input Components
- [ ] Input field
- [ ] Select dropdown
- [ ] Checkbox
- [ ] Radio button
- [ ] Date picker
- [ ] File upload

## Faza 3: Layout Components

### 3.1 Layout Component
- [ ] Ažurirati Layout komponentu
- [ ] Sidebar navigation
- [ ] Header/Topbar
- [ ] Main content area
- [ ] Footer (opciono)

### 3.2 Navigation Component
- [ ] Ažurirati Navigation komponentu
- [ ] Menu items sa ikonama
- [ ] Active state
- [ ] Collapsible sections
- [ ] Hover effects

## Faza 4: Pages

### 4.1 Dashboard
- [ ] Ažurirati Dashboard sa ggrock stilom
- [ ] Statistics cards
- [ ] Charts/Graphs
- [ ] Recent activity
- [ ] Quick actions

### 4.2 Images
- [ ] Ažurirati Images stranicu
- [ ] Image list table
- [ ] Create/Edit image modal
- [ ] Image details
- [ ] Snapshot management

### 4.3 Machines
- [ ] Ažurirati Machines stranicu
- [ ] Machine list table
- [ ] Machine details
- [ ] Boot configuration
- [ ] Status monitoring

### 4.4 VMs
- [ ] Ažurirati VMs stranicu
- [ ] VM list table
- [ ] VM details
- [ ] VM console (VNC)
- [ ] VM actions (start/stop/reset)

### 4.5 Storage
- [ ] Ažurirati Storage stranicu
- [ ] Pool status
- [ ] Dataset list
- [ ] ARC statistics
- [ ] IO statistics

### 4.6 Network
- [ ] Kreirati Network stranicu
- [ ] Network configuration
- [ ] iPXE boot setup
- [ ] iSCSI targets
- [ ] DNS configuration

### 4.7 Settings
- [ ] Ažurirati Settings stranicu
- [ ] Settings list
- [ ] Create/Edit setting
- [ ] Bulk update
- [ ] Categories

### 4.8 Clients
- [ ] Kreirati Clients stranicu
- [ ] Client list
- [ ] Client details
- [ ] Client status
- [ ] Real-time updates

## Faza 5: Styling

### 5.1 Global Styles
- [ ] Ažurirati global styles
- [ ] Typography
- [ ] Spacing
- [ ] Shadows
- [ ] Animations

### 5.2 Component Styles
- [ ] Stilizovati sve komponente
- [ ] Consistent spacing
- [ ] Consistent colors
- [ ] Consistent typography
- [ ] Consistent shadows
- [ ] Consistent borders

## Faza 6: Functionality

### 6.1 API Integration
- [ ] Sve API pozive kroz service layer
- [ ] Error handling
- [ ] Loading states
- [ ] Success/Error notifications

### 6.2 Real-time Updates
- [ ] WebSocket connection
- [ ] Live status updates
- [ ] Live data refresh

### 6.3 User Experience
- [ ] Loading indicators
- [ ] Error messages
- [ ] Success messages
- [ ] Confirmation dialogs
- [ ] Form validation

## Prioriteti

### Visok Prioritet
1. Design System CSS varijable ✅
2. Base Components (Button, Card, Table, Modal)
3. Layout Components (Layout, Navigation)
4. Dashboard stranica
5. Images stranica
6. Machines stranica

### Srednji Prioritet
7. VMs stranica
8. Storage stranica
9. Settings stranica
10. Network stranica

### Nizak Prioritet
11. Clients stranica
12. i18n podrška (opciono)
13. Animations
14. Advanced features

## Sledeći Koraci

1. **Kreirati Button komponentu** sa ggrock stilom
2. **Kreirati Card komponentu** sa ggrock stilom
3. **Ažurirati Layout komponentu** sa ggrock stilom
4. **Ažurirati Dashboard stranicu** sa ggrock stilom
5. **Ažurirati Images stranicu** sa ggrock stilom

## Napomene

- **Framework**: ggrock koristi Angular, ggnet2 koristi React
- **Build Tool**: ggrock koristi Angular CLI, ggnet2 koristi Vite
- **State Management**: ggrock koristi Angular services, ggnet2 koristi Zustand
- **Styling**: ggrock koristi CSS varijable, ggnet2 će koristiti CSS varijable
- **Theme**: Oba koriste dark theme sa sličnim bojama

