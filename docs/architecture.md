# Documento di Architettura - Applicazione Todo

## Panoramica

L'applicazione Todo è una soluzione full-stack moderna per la gestione di attività personali. Implementa un'architettura client-server con frontend React e backend .NET 8, distribuita su Azure con infrastruttura containerizzata e storage persistente.

L'applicazione consente agli utenti di creare, visualizzare, modificare, eliminare e completare attività in modo intuitivo, con sincronizzazione in tempo reale e persistenza dei dati.

---

## Requisiti Funzionali

### Gestione Todo

- **Visualizzazione lista**: Mostrare tutti i todo dell'utente con titolo e stato di completamento
- **Creazione**: Aggiungere nuovi todo tramite form con validazione del titolo
- **Modifica**: Editare il titolo di un todo esistente tramite modal
- **Eliminazione**: Rimuovere todo con conferma preventiva
- **Toggle completamento**: Marcare/smarcare un todo come completato con cambio visivo immediato

### Esperienza Utente

- Caricamento dati al mount del componente
- Gestione errori di caricamento con messaggi informativi
- Messaggi di successo per operazioni completate
- Form resettato dopo submit
- Possibilità di annullare modifiche
- Stili visivi differenti per todo completati

---

## Requisiti Non Funzionali

### Performance

- Tempo di risposta API inferiore a 500ms
- Caricamento lista entro 2 secondi
- Supporto fino a 10.000 todo per utente

### Affidabilità

- Disponibilità minima 99%
- Persistenza garantita dei dati
- Backup automatico del database
- Health check ogni 10 secondi

### Scalabilità

- Auto-scaling da 1 a 3 repliche del backend
- Supporto per crescita futura di utenti
- Architettura stateless per il backend

### Sicurezza

- HTTPS obbligatorio
- CORS configurato per domini autorizzati
- Rate limiting: 100 richieste per minuto
- Validazione input lato server
- Prevenzione SQL injection tramite EF Core
- Gestione secrets con Azure Key Vault

### Manutenibilità

- Codice documentato e testato
- Migrazioni database versionabili
- Logging centralizzato con Application Insights
- CI/CD automatizzato con GitHub Actions

---

## Architettura Logica

### Livelli Applicativi

**Presentation Layer (Frontend)**
- Componenti React per UI
- Custom hook useTodos per gestione stato
- Client HTTP Axios per comunicazione API
- Styling con Tailwind CSS

**API Layer (Backend)**
- Minimal API .NET 8
- Endpoint RESTful per operazioni CRUD
- Validazione richieste
- Gestione errori centralizzata

**Business Logic Layer**
- TodoService per logica di business
- Validazioni di dominio
- Orchestrazione operazioni

**Data Access Layer**
- Entity Framework Core ORM
- TodoContext per accesso database
- Migrazioni database
- Query ottimizzate con indici

**Data Layer**
- SQLite per persistenza
- Tabella Todo con campi Id, Title, IsCompleted, CreatedAt, UpdatedAt
- Indici su CreatedAt e IsCompleted

### Flusso Dati

1. Frontend invia richiesta HTTP tramite Axios
2. Backend riceve e valida richiesta
3. TodoService elabora logica business
4. EF Core interagisce con SQLite
5. Risposta ritorna al frontend
6. React aggiorna stato e UI

---

## Architettura Fisica (Azure)

### Componenti Infrastrutturali

**Container App (todo-api)**
- Hosting backend .NET 8
- CPU: 0.5 core
- Memoria: 1GB
- Repliche: 1-3 (auto-scaling)
- Porta: 8080
- Health probe HTTP ogni 10 secondi
- Immagine da Azure Container Registry

**Static Web App (todo-frontend)**
- Hosting frontend React
- Build automatico da GitHub
- Distribuzione globale tramite CDN
- SKU Standard
- Integrazione CI/CD nativa

**Container Registry (ACR)**
- Nome: crsharedacrcorchn001
- SKU: Standard
- Repository: todo-api
- Gestione versioni immagini

**Storage Account (todo-db)**
- Backup SQLite
- SKU: Standard_LRS
- Tipo: StorageV2
- Tier: Hot

**Key Vault (todo-keyvault)**
- Gestione secrets
- Connection string database
- SKU: Standard

**Application Insights (todo-appinsights)**
- Monitoring e logging
- Retention: 30 giorni
- Metriche custom
- Alert configurati

### Rete e Connettività

- Regione: West Europe
- Resource Group: rg-todo-app
- CORS abilitato per domini autorizzati
- HTTPS obbligatorio
- Ingress esterno per Container App

---

## Flussi Principali

### Flusso 1: Visualizzazione Lista Todo

1. Utente accede all'applicazione
2. Componente TodoList monta
3. Hook useTodos chiama API GET /todos
4. Backend recupera todo da SQLite
5. Risposta JSON ritorna al frontend
6. React renderizza lista con TodoItem per ogni elemento
7. Se lista vuota, mostra messaggio appropriato
8. Se errore, mostra notifica di errore

### Flusso 2: Creazione Nuovo Todo

1. Utente compila form con titolo
2. Bottone submit disabilitato se titolo vuoto
3. Submit invia POST /todos con payload {title}
4. Backend valida titolo (1-255 caratteri)
5. TodoService crea nuovo Todo
6. EF Core salva in SQLite
7. API ritorna todo creato con id
8. Frontend aggiunge todo in cima alla lista
9. Form resettato
10. Messaggio di successo visualizzato

### Flusso 3: Modifica Todo

1. Utente clicca su todo
2. Modal edit apre con titolo pre-compilato
3. Utente modifica titolo
4. Validazione titolo non vuoto
5. Submit invia PUT /todos/{id} con {title, isCompleted}
6. Backend valida e aggiorna
7. EF Core salva in SQLite
8. API ritorna todo aggiornato
9. Frontend aggiorna lista in tempo reale
10. Modal chiude
11. Messaggio di successo

### Flusso 4: Eliminazione Todo

1. Utente clicca bottone delete
2. Modal di conferma appare
3. Utente conferma eliminazione
4. Frontend invia DELETE /todos/{id}
5. Backend elimina da SQLite
6. API ritorna 204 No Content
7. Frontend rimuove todo dalla lista
8. Messaggio di successo visualizzato

### Flusso 5: Toggle Completamento

1. Utente clicca checkbox su todo
2. Frontend invia PATCH /todos/{id}/toggle
3. Backend inverte isCompleted
4. EF Core salva in SQLite
5. API ritorna todo aggiornato
6. Frontend aggiorna stato immediato
7. Stile visivo cambia (strikethrough, opacità)
8. Persistenza garantita

---

## Sicurezza e Scalabilità

### Misure di Sicurezza

**Autenticazione e Autorizzazione**
- Attualmente nessuna autenticazione (pubblico)
- Pronto per integrazione OAuth2/JWT
- CORS limita accesso a domini autorizzati

**Protezione Dati**
- HTTPS obbligatorio su tutti i canali
- Secrets gestiti in Azure Key Vault
- Connection string non hardcoded
- Variabili ambiente per configurazione sensibile

**Validazione Input**
- Titolo obbligatorio e lunghezza 1-255 caratteri
- Validazione lato server con EF Core
- Prevenzione SQL injection tramite query parametrizzate
- Rate limiting: 100 richieste/minuto

**Logging e Monitoring**
- Application Insights traccia errori
- Log level: Information
- Alert su error rate > 5%
- Audit trail delle operazioni

### Strategie di Scalabilità

**Orizzontale (Backend)**
- Auto-scaling Container App: 1-3 repliche
- Load balancing automatico
- Stateless design per facilità scaling
- Nessuna sessione locale

**Verticale (Database)**
- Indici su CreatedAt e IsCompleted
- Query ottimizzate
- Possibilità migrazione a SQL Server
- Backup automatico su Storage Account

**Frontend**
- CDN globale tramite Static Web App
- Caching assets statici
- Lazy loading componenti
- Ottimizzazione bundle

**API**
- Endpoint RESTful leggeri
- Minimal API riduce overhead
- Compressione response
- Caching HTTP headers

### Monitoraggio Scalabilità

- Metrica TodoCreated: conteggio creazioni
- Metrica TodoDeleted: conteggio eliminazioni
- Metrica ApiResponseTime: istogramma latenza
- Alert su memory usage > 80%
- Alert su availability < 99%

---

## Deployment e CI/CD

### Pipeline GitHub Actions

**Trigger**: Push su branch main

**Stage 1: Build Backend**
- Checkout codice
- Setup .NET 8
- Restore dipendenze
- Build soluzione
- Esecuzione test xUnit
- Publish artefatti

**Stage 2: Build Frontend**
- Checkout codice
- Setup Node 18
- Install dipendenze npm
- Esecuzione test Jest
- Build React (output: build/)

**Stage 3: Push to ACR**
- Docker build immagine
- Tag: crsharedacrcorchn001.azurecr.io/todo-api:latest
- Push a Azure Container Registry

**Stage 4: Deploy Backend**
- Deploy Container App
- Aggiornamento immagine
- Health check automatico

**Stage 5: Deploy Frontend**
- Deploy Static Web App
- Publish artefatti build/
- Invalidazione cache CDN

---

## Tecnologie Stack

### Backend
- Runtime: .NET 8
- Framework: Minimal API
- ORM: Entity Framework Core 8.0
- Database: SQLite
- Testing: xUnit + Moq

### Frontend
- Runtime: Node 18.x
- Framework: React 18
- HTTP Client: Axios 1.x
- Styling: Tailwind CSS 3.x
- Testing: Jest + React Testing Library

### Infrastruttura
- Container: Docker
- Orchestrazione: Azure Container Apps
- Registry: Azure Container Registry
- Hosting Frontend: Azure Static Web App
- Storage: Azure Storage Account
- Secrets: Azure Key Vault
- Monitoring: Azure Application Insights
- CI/CD: GitHub Actions

---

## Conclusioni

L'architettura proposta fornisce una soluzione scalabile, sicura e manutenibile per la gestione di todo. La separazione netta tra frontend e backend, combinata con l'infrastruttura Azure, garantisce affidabilità, performance e facilità di evoluzione futura. Il design stateless del backend consente scaling orizzontale trasparente, mentre il database SQLite offre semplicità con possibilità di migrazione verso soluzioni più robuste.