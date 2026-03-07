# Documento di Architettura - Applicazione Todo

## 1. Panoramica

L'applicazione Todo è una soluzione full-stack moderna per la gestione di attività personali. Implementa un'architettura a tre livelli con frontend React, backend .NET 8 e database SQLite, deployata su Azure Container Apps e Static Web App.

L'applicazione consente agli utenti di creare, visualizzare, modificare, eliminare e completare attività attraverso un'interfaccia web intuitiva e responsiva.

---

## 2. Requisiti Funzionali

### 2.1 Gestione Todo

- **Visualizzazione lista**: L'utente visualizza tutti i todo con titolo e stato completamento
- **Creazione**: Aggiunta di nuovi todo tramite form con titolo obbligatorio
- **Modifica**: Editing del titolo di un todo esistente con conferma
- **Eliminazione**: Rimozione di todo con conferma preventiva
- **Toggle completamento**: Marcatura di todo come completato/non completato

### 2.2 Validazione

- Titolo obbligatorio e lunghezza tra 1 e 255 caratteri
- Validazione lato client e server
- Messaggi di errore chiari all'utente

### 2.3 Esperienza Utente

- Caricamento automatico della lista al mount del componente
- Aggiornamento istantaneo dell'interfaccia dopo operazioni
- Gestione degli errori API con feedback visivo
- Reset del form dopo creazione con successo

---

## 3. Requisiti Non Funzionali

### 3.1 Performance

- Tempo di risposta API inferiore a 2 secondi
- Caricamento della pagina entro 3 secondi
- Supporto fino a 10.000 todo per utente

### 3.2 Affidabilità

- Disponibilità del servizio 99.5%
- Rollback automatico in caso di errore durante modifica
- Gestione graceful dei timeout API

### 3.3 Scalabilità

- Auto-scaling da 1 a 3 repliche del backend
- Supporto per crescita futura di utenti
- Database SQLite con indici ottimizzati

### 3.4 Sicurezza

- HTTPS obbligatorio (TLS 1.2+)
- CORS configurato per domini autorizzati
- Secrets gestiti in Azure KeyVault
- Nessuna autenticazione richiesta (app pubblica)

### 3.5 Manutenibilità

- Copertura test backend 80%
- Copertura test frontend 75%
- Documentazione API con OpenAPI 3.0
- Logging centralizzato con Application Insights

---

## 4. Architettura Logica

### 4.1 Livelli Applicativi

**Presentation Layer (Frontend)**
- Componenti React per visualizzazione e interazione
- Gestione dello stato locale con hooks
- Validazione lato client
- Styling con Tailwind CSS

**Business Logic Layer (Backend)**
- Servizi per logica di business
- Validazione dati
- Orchestrazione operazioni database
- Gestione errori e logging

**Data Access Layer (Backend)**
- Entity Framework Core per ORM
- Migrations per versionamento schema
- Query ottimizzate con indici
- Transazioni per consistenza dati

**Data Layer**
- SQLite come database relazionale
- Tabella Todo con campi Id, Title, IsCompleted, CreatedAt, UpdatedAt

### 4.2 Componenti Frontend

**TodoList**: Componente principale che gestisce la lista, lo stato di caricamento e gli errori

**TodoItem**: Elemento singolo con azioni di modifica, eliminazione e toggle

**TodoForm**: Form riutilizzabile per creazione e modifica con validazione

**useTodos Hook**: Logica centralizzata per comunicazione con API e gestione stato

### 4.3 Endpoint API

- GET /todos: Recupera lista completa
- POST /todos: Crea nuovo todo
- GET /todos/{id}: Recupera singolo todo
- PUT /todos/{id}: Aggiorna titolo
- DELETE /todos/{id}: Elimina todo
- PATCH /todos/{id}/toggle: Toggle completamento
- GET /health: Health check per monitoring

---

## 5. Architettura Fisica (Azure)

### 5.1 Componenti Azure

**Azure Container Apps (todo-api)**
- Hosting del backend .NET 8
- CPU: 0.5 core, Memoria: 1GB
- Auto-scaling: 1-3 repliche
- Ingress esterno sulla porta 8080
- Health check ogni 10 secondi

**Azure Static Web App (todo-frontend)**
- Hosting del frontend React
- Build automatico da GitHub
- CDN globale per distribuzione
- Custom domain: todo.example.com
- HTTPS obbligatorio

**Azure Container Registry (crsharedacrcorchn001)**
- Registro centralizzato per immagini Docker
- Versioning con tag latest
- Accesso da Container Apps

**Azure KeyVault (keyvault-todo)**
- Gestione centralizzata secrets
- Connection string database
- API keys
- Rotazione automatica ogni 90 giorni

**Application Insights (appinsights-todo)**
- Monitoring e logging centralizzato
- Retention 30 giorni
- Sampling al 100%
- Metriche custom e alert

### 5.2 Flusso Deployment

GitHub Actions monitora il branch main e triggera pipeline automatica:

1. Build Backend: Compilazione .NET, test, build immagine Docker, push su ACR
2. Build Frontend: Setup Node, test, build production, deploy su Static Web App
3. Deploy Backend: Aggiornamento Container App, smoke test, notifiche

---

## 6. Flussi Principali

### 6.1 Flusso Visualizzazione Todo

1. Utente accede all'applicazione
2. Componente TodoList monta e chiama useTodos hook
3. Hook esegue GET /todos verso API
4. Backend recupera dati da database
5. Risposta JSON con array di todo
6. Frontend renderizza lista con Tailwind CSS
7. Gestione errore se API non disponibile

### 6.2 Flusso Creazione Todo

1. Utente compila form con titolo
2. Validazione lato client (lunghezza, non vuoto)
3. Submit invia POST /todos con payload JSON
4. Backend valida dati
5. TodoService crea record in database
6. Database ritorna todo con Id generato
7. Frontend aggiunge todo in lista
8. Form resetta per nuova creazione
9. Feedback visivo di successo

### 6.3 Flusso Modifica Todo

1. Utente clicca edit su todo
2. Modal/inline edit mostra titolo attuale
3. Utente modifica testo
4. Validazione lato client
5. Submit invia PUT /todos/{id} con nuovo titolo
6. Backend valida e aggiorna record
7. Frontend aggiorna todo in lista
8. Rollback UI se errore API
9. Conferma visiva di salvataggio

### 6.4 Flusso Eliminazione Todo

1. Utente clicca delete su todo
2. Modal di conferma chiede conferma
3. Utente conferma eliminazione
4. DELETE /todos/{id} inviato al backend
5. Backend rimuove record da database
6. Frontend rimuove todo da lista
7. Gestione errore se eliminazione fallisce

### 6.5 Flusso Toggle Completamento

1. Utente clicca checkbox su todo
2. PATCH /todos/{id}/toggle inviato
3. Backend inverte IsCompleted
4. Frontend aggiorna UI istantaneamente
5. Stile differente per todo completati (strikethrough, opacità)
6. Aggiornamento senza reload pagina

---

## 7. Sicurezza e Scalabilità

### 7.1 Sicurezza

**Comunicazione**
- HTTPS obbligatorio su tutti gli endpoint
- TLS 1.2 come versione minima
- Certificati gestiti da Azure

**CORS**
- Whitelist di domini autorizzati
- Metodi HTTP limitati (GET, POST, PUT, DELETE, PATCH)
- Headers Content-Type e Authorization consentiti

**Secrets Management**
- Connection string in Azure KeyVault
- Variabili d'ambiente per configurazione sensibile
- Nessun secret in codice sorgente
- Rotazione automatica ogni 90 giorni

**Autenticazione**
- App pubblica senza autenticazione
- Nessun token JWT o API key richiesto
- Adatto per uso personale/demo

### 7.2 Scalabilità

**Backend**
- Auto-scaling da 1 a 3 repliche in Container Apps
- Load balancing automatico tra repliche
- Stateless design per scalabilità orizzontale
- Database SQLite con indice su CreatedAt

**Frontend**
- CDN globale di Static Web App
- Caching di asset statici
- Lazy loading di componenti
- Ottimizzazione bundle con Vite

**Database**
- SQLite adatto per carichi moderati
- Indice su CreatedAt per query efficienti
- Possibilità di migrazione a SQL Server in futuro
- Backup automatico tramite Azure

### 7.3 Monitoring e Osservabilità

**Application Insights**
- Tracciamento di tutte le richieste API
- Metriche custom: TodoCreated, TodoDeleted, ApiResponseTime
- Logging centralizzato con livello Information
- Retention 30 giorni

**Alert**
- Notifica se error rate > 5%
- Notifica se response time > 2 secondi
- Email notification per escalation

**Health Check**
- Endpoint /health controllato ogni 10 secondi
- Timeout 5 secondi, threshold 3 fallimenti
- Restart automatico di repliche non healthy

### 7.4 Disaster Recovery

**Backup**
- Database SQLite con snapshot giornaliero
- Codice sorgente versionato su GitHub
- Immagini Docker in Container Registry

**Rollback**
- Versioning di immagini Docker con tag
- Possibilità di rollback a versione precedente
- Zero-downtime deployment con blue-green

---

## 8. Tecnologie Stack

### Backend
- Framework: .NET 8 con Minimal API
- ORM: Entity Framework Core 8.0
- Database: SQLite
- Testing: xUnit
- Logging: Application Insights

### Frontend
- Framework: React 18+
- Styling: Tailwind CSS
- Build Tool: Vite
- Testing: Jest
- HTTP Client: Fetch API

### Infrastructure
- Container Orchestration: Azure Container Apps
- Static Hosting: Azure Static Web App
- Registry: Azure Container Registry
- Secrets: Azure KeyVault
- Monitoring: Application Insights
- CI/CD: GitHub Actions

---

## 9. Roadmap Futura

- Autenticazione utente con Azure AD
- Migrazione a SQL Server per carichi elevati
- Sincronizzazione offline con Service Worker
- Categorie e tag per todo
- Condivisione liste con altri utenti
- Mobile app nativa
- Notifiche push per reminder