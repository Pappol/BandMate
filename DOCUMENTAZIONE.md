# DOCUMENTAZIONE BANDMATE - Sistema di Gestione Band Musicali

## 📋 PANORAMICA DEL PROGETTO

**BandMate** è un'applicazione web per la gestione di band musicali che permette ai membri di:
- Tracciare il progresso nell'apprendimento delle canzoni
- Gestire una wishlist di brani da imparare
- Generare setlist ottimizzate per le prove
- Coordinare le attività della band

## 🎯 REQUISITI FUNZIONALI

### Autenticazione e Gestione Utenti
- [x] Login con Google OAuth
- [x] Sistema di ruoli (band leader, membro)
- [x] Onboarding per nuovi utenti
- [x] Gestione sessioni

### Gestione Band
- [x] Creazione di nuove band
- [x] Invito di membri (sistema base)
- [x] Gestione ruoli e permessi

### Gestione Canzoni
- [x] Aggiunta canzoni alla wishlist
- [x] Sistema di votazione per le canzoni
- [x] Tracciamento progresso per membro
- [x] Stati delle canzoni (wishlist, attiva, archiviata)

### Dashboard e Monitoraggio
- [x] Dashboard principale con progresso
- [x] Visualizzazione stato canzoni per membro
- [x] Metriche di apprendimento

### Generazione Setlist
- [x] Algoritmo di ottimizzazione setlist
- [x] Bilanciamento tempo apprendimento vs manutenzione
- [x] Considerazione readiness score

## 🏗️ ARCHITETTURA E DESIGN

### Stack Tecnologico
- **Backend**: Flask (Python)
- **Database**: SQLite (sviluppo) / PostgreSQL (produzione)
- **Autenticazione**: Flask-Login + Flask-Dance (Google OAuth)
- **Frontend**: HTML + CSS + JavaScript vanilla
- **Database ORM**: SQLAlchemy

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
└── duration_minutes

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

## 🚧 TASK OPERATIVI DA COMPLETARE

### 🔴 PRIORITÀ ALTA - OAuth e Autenticazione
- [x] **RISOLVERE LOOP DI REDIRECT GOOGLE OAUTH** ✅
  - Problema: Troppi redirect durante il login
  - Causa: Configurazione errata delle route OAuth e route duplicate
  - Soluzione: Riorganizzato il flusso OAuth, rimosso route duplicate, aggiunto logging debug
  - Status: RISOLTO - 29 Agosto 2025

- [ ] Implementare gestione errori OAuth robusta
- [ ] Aggiungere logout OAuth completo
- [ ] Testare flusso completo di autenticazione

### 🟡 PRIORITÀ MEDIA - Funzionalità Core
- [ ] **Sistema di Inviti per Band**
  - Generazione codici invito univoci
  - Validazione codici invito
  - Notifiche email (opzionale)

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

- [ ] **Mobile Responsiveness**
  - Ottimizzazione per dispositivi mobili
  - PWA capabilities

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
- [ ] Test completi autenticazione
- [ ] Documentazione API

### Fase 2: Funzionalità Core (Settimana 3-4)
- [ ] Sistema inviti band
- [ ] Notifiche base
- [ ] Miglioramenti dashboard

### Fase 3: Ottimizzazioni (Settimana 5-6)
- [ ] Performance tuning
- [ ] Mobile responsiveness
- [ ] Test di carico

## 📝 NOTE DI SVILUPPO

### Ultimo Aggiornamento
- **Data**: 29 Agosto 2025
- **Versione**: 0.1.0-alpha
- **Sviluppatore**: AI Assistant

### Prossima Sessione
- **Focus**: Test autenticazione OAuth e gestione errori
- **Obiettivo**: Sistema di autenticazione completamente stabile
- **Tempo Stimato**: 1-2 ore

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

## 🔍 RISORSE E RIFERIMENTI

### Documentazione
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask-Dance OAuth](https://flask-dance.readthedocs.io/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

### Strumenti di Sviluppo
- **IDE**: Cursor (AI-powered)
- **Database**: SQLite Browser
- **Testing**: pytest
- **Versioning**: Git

---

*Questo documento deve essere aggiornato ad ogni sessione di sviluppo per mantenere traccia dello stato del progetto.*
