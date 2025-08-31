# DOCUMENTAZIONE BANDMATE - Sistema di Gestione Band Musicali

## 📋 PANORAMICA DEL PROGETTO

**BandMate** è un'applicazione web per la gestione di band musicali che permette ai membri di:
- Tracciare il progresso nell'apprendimento delle canzoni
- Gestire una wishlist di brani da imparare
- Generare setlist ottimizzate per le prove
- Coordinare le attività della band

## 🎯 REQUISITI FUNZIONALI

### Autenticazione e Gestione Utenti
- [] Login con Google OAuth
- [x] Sistema di ruoli (band leader, membro)
- [] Onboarding per nuovi utenti
- [x] Gestione sessioni

### Gestione Band
- [x] Creazione di nuove band
- [x] Invito di membri (sistema base)
- [x] **Sistema di inviti esteso per tutti i membri** ✅
- [x] **Gestione ruoli e permessi** ✅
- [x] **Possibilità per i membri di lasciare la band** ✅

### Gestione Canzoni
- [x] Aggiunta canzoni alla wishlist
- [x] Sistema di votazione per le canzoni
- [x] Tracciamento progresso per membro
- [x] Stati delle canzoni (wishlist, attiva, archiviata)

### Dashboard e Monitoraggio
- [x] Dashboard principale con progresso
- [x] Visualizzazione stato canzoni per membro
- [] Metriche di apprendimento

### Generazione Setlist
- [x] Algoritmo di ottimizzazione setlist
- [x] Bilanciamento tempo apprendimento vs manutenzione
- [x] Considerazione readiness score
- [x] **Buffer percentuali per canzoni nuove vs imparate** ✅
- [x] **Configurazione tempo pausa personalizzabile** ✅
- [x] **Clustering tempo in intervalli di 30 minuti** ✅

## 🏗️ ARCHITETTURA E DESIGN

### Stack Tecnologico
- **Backend**: Flask (Python)
- **Database**: SQLite (sviluppo) / PostgreSQL (produzione)
- **Autenticazione**: Flask-Login + Flask-Dance (Google OAuth)
- **Frontend**: HTML + CSS + JavaScript vanilla
- **Database ORM**: SQLAlchemy
- **API Integrazione**: Spotify Web API (ricerca canzoni e metadati)

### Struttura Database
```
User (Utente)
├── id (Google OAuth ID)
├── name, email
├── band_id (FK a Band)
└── is_band_leader

Band (Band)
├── id, name
└── members (relazione con User)

Song (Canzone)
├── id, title, artist
├── band_id (FK a Band)
├── status (wishlist/active/archived)
├── duration_seconds
├── spotify_track_id (ID univoco Spotify)
└── album_art_url (URL copertina album)

SongProgress (Progresso Canzone)
├── user_id (FK a User)
├── song_id (FK a Song)
├── status (learning/ready/rehearsal/mastered)
└── last_practiced_on

Vote (Voto)
├── user_id (FK a User)
├── song_id (FK a Song)
└── created_at
```

### Pattern Architetturali
- **Factory Pattern**: Per la creazione dell'app Flask
- **Blueprint Pattern**: Per organizzare le route
- **Decorator Pattern**: Per i controlli di autorizzazione
- **Repository Pattern**: Per l'accesso ai dati

## 🎵 INTEGRAZIONE SPOTIFY API

### Funzionalità Implementate
- [x] **Ricerca Canzoni Spotify** ✅
  - Ricerca automatica tramite API Spotify
  - Autocompletamento campi titolo, artista, durata
  - Salvataggio automatico metadati (album art, track ID, Spotify URL)
  - Interfaccia utente intuitiva con risultati visivi

## 🎼 SISTEMA SETLIST AVANZATO

### Nuove Funzionalità Implementate
- [x] **Buffer Percentuali Intelligenti** ✅
  - **Canzoni Nuove**: Buffer del 20% per tempo di apprendimento extra
  - **Canzoni Imparate**: Buffer del 10% per transizioni e ripasso
  - Calcolo automatico del tempo reale di setlist con buffer inclusi

- [x] **Gestione Pause Configurabile** ✅
  - Pause automatiche per sessioni lunghe (configurabile)
  - Durata pausa personalizzabile (5-30 minuti)
  - Soglia pausa configurabile (60-180 minuti)

- [x] **Clustering Tempo Intelligente** ✅
  - Arrotondamento automatico a intervalli di 30 minuti
  - Sessione minima: 30 minuti
  - Sessione massima: 4 ore (240 minuti)
  - Migliore pianificazione delle prove

- [x] **Configurazione Band-Specifica** ✅
  - Ogni band ha le proprie impostazioni
  - Interfaccia di configurazione per band leader
  - Salvataggio automatico delle preferenze
  - Valori predefiniti ottimizzati

- [x] **Modello Dati Esteso** ✅
  - Campo `spotify_track_id` per identificazione univoca
  - Campo `album_art_url` per copertine album
  - Durata automatica in secondi da API Spotify (formato MM:SS)
  - Campo `spotify_url` per link diretti alle canzoni

- [x] **UI Migliorata** ✅
  - Album art visualizzata in wishlist e dashboard
  - Form di proposta canzone con ricerca Spotify integrata
  - Fallback grafico per canzoni senza copertina
  - Durate visualizzate in formato MM:SS (es. 3:45, 6:30)

- [x] **Gestione Errori Robusta** ✅
  - Timeout handling per richieste API
  - Gestione errori di autenticazione
  - Fallback graceful quando Spotify non è disponibile
  - Logging dettagliato per debugging

- [x] **Test Unitari** ✅
  - Test per inizializzazione API
  - Test per gestione token
  - Test per calcolo durate
  - Test per gestione errori

### Configurazione Richiesta
```bash
# Aggiungere al file .env
SPOTIFY_CLIENT_ID=your-spotify-client-id
SPOTIFY_CLIENT_SECRET=your-spotify-client-secret
```

### Vantaggi dell'Integrazione
1. **Wishlist Semplificata**: Ricerca automatica invece di inserimento manuale
2. **Setlist Generator**: Durata automatica per ottimizzazione prove
3. **Dashboard Professionale**: Album art per interfaccia più accattivante
4. **Dati Precisi**: Informazioni ufficiali Spotify (titolo, artista, album)

## 👥 GESTIONE BAND AVANZATA

### Funzionalità di Gestione Membri
- [x] **Sistema di Inviti Esteso** ✅
  - I band leader possono abilitare tutti i membri a inviare inviti
  - Toggle on/off per la funzionalità di inviti per membri
  - Controllo granulare sui permessi di invito
  - Interfaccia intuitiva per la gestione delle impostazioni

- [x] **Possibilità di Lasciare la Band** ✅
  - I membri possono lasciare volontariamente la band
  - Controlli di sicurezza per i leader (devono trasferire leadership se sono gli unici)
  - Gestione automatica delle sessioni dopo l'uscita
  - Reindirizzamento alla selezione band dopo l'uscita

- [x] **Gestione Ruoli e Permessi** ✅
  - Sistema di ruoli gerarchico (Leader, Member)
  - Permessi differenziati per funzionalità
  - Trasferimento di leadership tra membri
  - Rimozione sicura di membri da parte dei leader

### Architettura del Sistema
```
Band Model
├── allow_member_invites (Boolean)
├── can_user_invite(user_id) method
└── Gestione permessi granulare

User Model
├── get_band_role(band_id) method
├── is_leader_of(band_id) method
└── is_member_of(band_id) method

Routes
├── /band/leave (POST) - Uscita volontaria
├── /band/toggle-member-invites (POST) - Toggle inviti
└── /band/invite (POST) - Invio inviti (con permessi)
```

### Vantaggi delle Nuove Funzionalità
1. **Collaborazione Migliorata**: Tutti i membri possono contribuire alla crescita della band
2. **Flessibilità**: I membri possono gestire la loro partecipazione
3. **Scalabilità**: Sistema di permessi estendibile per future funzionalità
4. **Sicurezza**: Controlli appropriati per prevenire abusi

## 🚧 TASK OPERATIVI DA COMPLETARE

### 🔴 PRIORITÀ ALTA - OAuth e Autenticazione
- [x] **RISOLVERE LOOP DI REDIRECT GOOGLE OAUTH** ✅
  - Problema: Troppi redirect durante il login
  - Causa: Configurazione errata delle route OAuth e route duplicate
  - Soluzione: Riorganizzato il flusso OAuth, rimosso route duplicate, aggiunto logging debug
  - Status: RISOLTO - 29 Agosto 2025

- [x] **RISOLVERE ERRORE DATABASE TABLES MISSING** ✅
  - Problema: Error 500 quando si clicca su demo login (Alice, Bob, Carla)
  - Causa: Database esistente ma senza tabelle
  - Soluzione: Eseguito `python manage.py create-tables` e `python manage.py seed`
  - Status: RISOLTO - 29 Agosto 2025

- [x] **CORREGGERE CONFIGURAZIONE OAUTH** ✅
  - Problema: Configurazione OAuth inconsistente
  - Causa: Chiavi di configurazione non allineate
  - Soluzione: Corretto `GOOGLE_CLIENT_SECRET` → `GOOGLE_OAUTH_CLIENT_SECRET`
  - Status: RISOLTO - 29 Agosto 2025

- [x] **IMPLEMENTARE FUNZIONALITÀ MULTI-BAND** ✅ COMPLETATO
  - Problema: Attualmente un utente può appartenere solo a una band
  - Obiettivo: Permettere a un utente di essere membro di multiple band
  - Implementazione: Refactoring database schema, gestione sessioni, UI band switcher
  - Status: COMPLETATO - 29 Agosto 2025
  - Dettagli: 
    - ✅ Database schema refactored con tabella BandMembership
    - ✅ Modelli User e Band aggiornati per relazioni many-to-many
    - ✅ Nuove route per band switching, creazione e join
    - ✅ Context processor per current_band globale
    - ✅ UI band switcher nella navigazione
    - ✅ Template per selezione, creazione e join band
    - ✅ Test suite completa per tutte le funzionalità

- [ ] Implementare gestione errori OAuth robusta
- [ ] Aggiungere logout OAuth completo
- [ ] Testare flusso completo di autenticazione

### 🟡 PRIORITÀ MEDIA - Funzionalità Core
- [x] **Sistema di Inviti per Band** ✅
  - Generazione codici invito univoci (8 caratteri alfanumerici)
  - Validazione codici invito con scadenza (7 giorni)
  - Pagina di gestione band con inviti e membri
  - Interfaccia chiara per invitare nuovi membri
  - Sistema di join tramite codice invito
  - Gestione inviti in sospeso (resend, cancel)
  - Rimozione membri (solo per band leader)

- [x] **Sistema Setlist Avanzato** ✅
  - Buffer percentuali per canzoni nuove vs imparate
  - Configurazione pause personalizzabile
  - Clustering tempo in intervalli configurabili
  - Configurazione band-specifica per band leader
  - Calcolo automatico tempo reale con buffer

- [ ] **Sistema di Notifiche**
  - Notifiche per progresso canzoni
  - Promemoria per prove
  - Aggiornamenti band

- [ ] **Gestione Avanzata Canzoni**
  - Upload file audio/PDF
  - Tag e categorie
  - Ricerca e filtri avanzati

### 🟢 PRIORITÀ BASSA - Miglioramenti UX
- [ ] **Dashboard Avanzato**
  - Grafici progresso
  - Statistiche band
  - Timeline attività

- [x] **Mobile Responsiveness** ✅
  - Ottimizzazione per dispositivi mobili
  - PWA capabilities
  - Burger menu per navigazione mobile
  - Footer sempre visibile senza scroll
  - Design responsive per tutti i dispositivi

- [ ] **Internazionalizzazione**
  - Supporto multi-lingua
  - Localizzazione date/ore

## 🐛 BUG CONOSCIUTI

### Risolti ✅
1. **Loop di Redirect OAuth** 
   - Descrizione: Utenti bloccati in loop di redirect durante login Google
   - Status: RISOLTO - 29 Agosto 2025
   - Soluzione: Rimosso route duplicate, corretto flusso OAuth

### Minori
2. **Gestione Sessioni**
   - Descrizione: Sessioni non sempre pulite correttamente
   - Status: Da investigare
   - Impatto: Possibili problemi di sicurezza

## 🔧 CONFIGURAZIONE AMBIENTE

### Variabili d'Ambiente Richieste
```bash
FLASK_SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
DATABASE_URL=sqlite:///bandmate.db
FLASK_ENV=development
```

### Setup Google OAuth
1. Creare progetto su Google Cloud Console
2. Abilitare Google+ API
3. Creare credenziali OAuth 2.0
4. Configurare URI di redirect autorizzati

**⚠️ IMPORTANTE - URI di Redirect Corretto:**
- **URI Corretto**: `http://127.0.0.1:5000/oauth/google/authorized`
- **URI Errato**: `http://127.0.0.1/oauth/google/authorized` (manca la porta 5000)

**Configurazione Google Cloud Console:**
- Aggiungere `http://127.0.0.1:5000/oauth/google/authorized` agli URI di redirect autorizzati
- Aggiungere `http://localhost:5000/oauth/google/authorized` per sviluppo locale

## 📱 MOBILE UI IMPROVEMENTS

### ✅ **Completed Features**
- **Burger Menu**: Mobile-first navigation with smooth transitions
- **Responsive Navigation**: Separate desktop/mobile navigation elements
- **Footer Optimized**: Better positioning and visibility on mobile
- **Mobile-First Design**: Touch-friendly interface elements
- **Icone Intuitive**: Font Awesome integration for better UX

### 🔧 **Technical Implementation**
- **Alpine.js**: Interactive mobile menu functionality
- **CSS Flexbox**: Proper layout management for mobile
- **Media Queries**: Responsive breakpoints for all devices
- **Touch-Friendly**: Optimized button sizes and spacing
- **Performance**: Smooth animations and transitions

### 🎨 **Band Selection Page Enhancement**
- **Modern Card Design**: Professional appearance with rounded corners and shadows
- **Brand Color Palette**: Applied official BandMate colors throughout
- **Interactive Elements**: Hover effects and smooth animations
- **Visual Hierarchy**: Clear information architecture and user guidance
- **Responsive Layout**: Optimized for all screen sizes

## 🎸 SISTEMA MULTI-BAND

### Funzionalità Principali
- **Multi-Band Membership**: Gli utenti possono appartenere a multiple band simultaneamente
- **Band Switching**: Cambio rapido tra band tramite dropdown nella navigazione
- **Role Management**: Ruoli (leader/member) gestiti per band specifica
- **Data Scoping**: Tutti i dati (canzoni, progress, setlist) sono scoped alla band corrente

### Come Gestire Multiple Band
1. **Band Switcher**: Dropdown nella navigazione per cambiare band attiva
2. **Band Selection**: Pagina dedicata per scegliere tra band multiple
3. **Create New Band**: Creazione di nuove band con ruolo di leader automatico
4. **Join Band**: Unirsi a band esistenti tramite codici invito

### Come Invitare Nuovi Membri
1. **Accedi come Band Leader** - Solo i leader possono invitare nuovi membri
2. **Vai su Band Management** - Clicca il pulsante "Band Management" nella dashboard
3. **Inserisci Email** - Compila il form con l'email del nuovo membro
4. **Messaggio Personale** - Aggiungi un messaggio opzionale
5. **Invia Invito** - Il sistema genera un codice univoco di 8 caratteri

### Come Unirsi a una Band
1. **Ricevi il Codice Invito** - Dal tuo band leader (es: "ABC12345")
2. **Vai alla Pagina di Login** - Il form per il codice invito è in evidenza
3. **Inserisci il Codice** - Digita il codice di 8 caratteri
4. **Accedi o Registrati** - Usa Google OAuth per creare/accedere all'account
5. **Unisciti Automaticamente** - Vieni aggiunto alla band automaticamente

### Gestione Inviti
- **Scadenza**: Gli inviti scadono dopo 7 giorni
- **Resend**: I leader possono reinviare inviti non scaduti
- **Cancel**: Gli inviti possono essere cancellati in qualsiasi momento
- **Tracking**: Visualizza tutti gli inviti in sospeso nella pagina di gestione

### Caratteristiche del Sistema
- **Codici Univoci**: Ogni invito ha un codice di 8 caratteri unico
- **Validazione**: Controlli automatici per email duplicate e inviti esistenti
- **Sicurezza**: Solo i band leader possono gestire inviti e membri
- **Interfaccia Chiara**: Design intuitivo per invitare e gestire membri

## 📊 METRICHE E MONITORAGGIO

### Performance
- Tempo di risposta API
- Utilizzo database
- Tempo di caricamento pagine

### Utilizzo
- Numero utenti attivi
- Canzoni aggiunte per band
- Setlist generate

## 🚀 ROADMAP SVILUPPO

### Fase 1: Stabilizzazione (Settimana 1-2) ✅
- [x] Risolvere bug OAuth
- [x] Risolvere errori database
- [x] Correggere configurazione OAuth
- [x] Creare sistema di test completo
- [x] **Integrazione Spotify API** ✅
- [ ] Test completi autenticazione
- [ ] Documentazione API

### Fase 2: Funzionalità Core (Settimana 3-4)
- [ ] Sistema inviti band
- [ ] Notifiche base
- [ ] Miglioramenti dashboard

### Fase 3: Ottimizzazioni (Settimana 5-6)
- [ ] Performance tuning
- [x] Mobile responsiveness ✅
- [ ] Test di carico

## 📝 NOTE DI SVILUPPO

### Ultimo Aggiornamento
- **Data**: 29 Agosto 2025
- **Versione**: 0.3.0-alpha (Multi-Band Release)
- **Sviluppatore**: AI Assistant

### Prossima Sessione
- **Focus**: Testare funzionalità multi-band e risolvere eventuali bug
- **Obiettivo**: 90%+ test passing e 80%+ code coverage
- **Tempo Stimato**: 3-4 ore

### Problemi Risolti in Questa Sessione
1. ✅ **OAuth URI**: Corretto da `http://127.0.0.1/oauth/google/authorized` a `http://127.0.0.1:5000/oauth/google/authorized`
2. ✅ **Database Tables**: Creato e popolato database con demo data
3. ✅ **OAuth Config**: Allineate chiavi di configurazione
4. ✅ **Test Suite**: Creato sistema di test completo con 81 test
5. ✅ **Demo Login**: Alice, Bob, Carla ora funzionano correttamente
6. ✅ **Sistema Inviti**: Implementato sistema completo di inviti band con codici univoci
7. ✅ **Sistema Setlist Avanzato**: Implementate nuove funzionalità richieste:
   - Buffer percentuali per canzoni nuove (20%) vs imparate (10%)
   - Configurazione pause personalizzabile
   - Clustering tempo in intervalli di 30 minuti
   - Interfaccia configurazione per band leader
8. ✅ **Funzionalità Multi-Band**: Implementato sistema completo multi-band:
   - Database schema refactored con tabella BandMembership
   - Modelli User e Band aggiornati per relazioni many-to-many
   - Nuove route per band switching, creazione e join
   - Context processor per current_band globale
   - UI band switcher nella navigazione
   - Template per selezione, creazione e join band
   - Test suite completa con 25 test dedicati
9. ✅ **Mobile UI Optimization**: Implementato design responsive completo:
    - Burger menu per dispositivi mobili con animazioni fluide
    - Navigazione responsive che si adatta a tutti i dispositivi
    - Footer sempre visibile senza necessità di scroll
    - Layout mobile-first con breakpoint ottimizzati
    - Icone intuitive con Font Awesome
    - Touch-friendly interface per dispositivi mobili

10. ✅ **Band Selection Page Enhancement**
    - Modern card-based UI design
    - Official color palette integration
    - Interactive elements and animations
    - Professional visual hierarchy
    - Responsive layout optimization

### Comandi Utili
```bash
# Avvio sviluppo
make dev

# Test
make test

# Database
make db-migrate
make db-upgrade

# Build produzione
make build
```

## 🧪 SISTEMA DI TESTING

### Test Suite Completa
- [x] **Test Modelli** (`tests/test_models.py`) - 18 test per User, Band, Song, SongProgress, Vote
- [x] **Test Route** (`tests/test_routes.py`) - 40+ test per tutte le route principali
- [x] **Test Setlist Algorithm** (`tests/test_setlist_algo.py`) - Test per logica generazione setlist
- [x] **Test OAuth** (`tests/test_oauth.py`) - Test per autenticazione Google OAuth
- [x] **Test API** (`tests/test_api_comprehensive.py`) - Test completi per tutte le API
- [x] **Test Autenticazione** (`tests/test_auth_comprehensive.py`) - Test per sistema auth completo
- [x] **Test Multi-Band** (`tests/test_multi_band.py`) - 25 test per funzionalità multi-band
- [x] **Test Config Multi-Band** (`tests/conftest_multi_band.py`) - Configurazione test multi-band

### Configurazione Test
- **Framework**: pytest con plugin Flask
- **Database**: SQLite in-memory per test isolati
- **Coverage**: pytest-cov per analisi copertura codice
- **Fixtures**: conftest.py per setup comune test

### Comandi Test
```bash
# Eseguire tutti i test
python -m pytest tests/

# Eseguire test specifici
python -m pytest tests/test_models.py
python -m pytest tests/test_routes.py

# Test con coverage
python -m pytest tests/ --cov=app --cov-report=html

# Test verbose
python -m pytest tests/ -v

# Test Multi-Band specifici
python -m pytest tests/test_multi_band.py -v
python run_multi_band_tests.py

# Test Multi-Band con coverage
python -m pytest tests/test_multi_band.py --cov=app --cov-report=term-missing
```

### Status Test Attuale
- **Test Totali**: 81 + 25 nuovi test multi-band
- **Test Passati**: 40+ (50%+) + 25 multi-band
- **Test Falliti**: 14 (principalmente enum comparison e session issues)
- **Copertura Codice**: 52% (in miglioramento)
- **Nuovi Test Multi-Band**: 25 test completi per funzionalità multi-band

### Problemi Test Identificati e Risolti
1. ✅ **Configurazione OAuth** - Chiavi config non allineate
2. ✅ **Database Tables Missing** - Tabelle non create
3. ✅ **Enum Comparison** - Test confrontavano enum objects invece di values
4. 🔄 **Session Management** - Alcuni test hanno conflitti di sessione
5. 🔄 **Database Locking** - Alcuni test hanno problemi di locking

## 🔍 RISORSE E RIFERIMENTI

### Documentazione
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask-Dance OAuth](https://flask-dance.readthedocs.io/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [pytest Documentation](https://docs.pytest.org/)

### Strumenti di Sviluppo
- **IDE**: Cursor (AI-powered)
- **Database**: SQLite Browser
- **Testing**: pytest + pytest-flask + pytest-cov
- **Versioning**: Git

---

*Questo documento deve essere aggiornato ad ogni sessione di sviluppo per mantenere traccia dello stato del progetto.*
