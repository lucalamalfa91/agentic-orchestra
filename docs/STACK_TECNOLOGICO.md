# Agentic Orchestra - Stack Tecnologico
## Guida Didattica all'Architettura

> **Documento per presentazione dello stack tecnologico**
> Una guida completa all'architettura multi-agente orchestrata da LangGraph

---

## 📋 Indice

1. [Visione d'insieme](#1-visione-dinsieme)
2. [Stack tecnologico base](#2-stack-tecnologico-base)
3. [Orchestrazione con LangGraph](#3-orchestrazione-con-langgraph)
4. [Sistema MCP (Model Context Protocol)](#4-sistema-mcp-model-context-protocol)
5. [Sistema RAG (Retrieval-Augmented Generation)](#5-sistema-rag-retrieval-augmented-generation)
6. [Architettura degli agenti](#6-architettura-degli-agenti)
7. [Flusso completo di generazione](#7-flusso-completo-di-generazione)
8. [Esempio pratico end-to-end](#8-esempio-pratico-end-to-end)

---

## 1. Visione d'insieme

### Cosa fa l'applicazione?

Agentic Orchestra è una **piattaforma di generazione automatica di MVP** (Minimum Viable Product) che trasforma una descrizione testuale in un'applicazione full-stack funzionante pubblicata su GitHub.

**Analogia**: Immagina un'orchestra sinfonica dove:
- Il **direttore d'orchestra** = LangGraph (coordina tutti)
- I **musicisti** = Agenti AI (ciascuno specializzato in un compito)
- Lo **spartito** = Requirements dell'utente
- La **memoria musicale** = Sistema RAG (conosce best practices e pattern)
- Gli **strumenti musicali** = MCP Servers (GitHub, Azure DevOps, Railway)

### Architettura ad alto livello

```
┌─────────────────────────────────────────────────────────────┐
│                     UTENTE (Frontend React)                  │
└───────────────────────────┬─────────────────────────────────┘
                            │ WebSocket + REST API
┌───────────────────────────▼─────────────────────────────────┐
│                  ORCHESTRATORE (FastAPI)                     │
│  • Gestisce WebSocket per progress streaming                │
│  • Inietta token/config come env vars                       │
│  • Avvia LangGraph execution                                │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│              LANGGRAPH (Grafo di Agenti)                     │
│                                                              │
│  START → Knowledge → Design → [Backend ∥ Frontend ∥ Backlog]│
│         → Integration → DevOps → Publish → END              │
│                                                              │
│  Ogni nodo = Agente autonomo                                │
└──────────────┬────────────────────────┬─────────────────────┘
               │                        │
       ┌───────▼────────┐      ┌────────▼────────┐
       │  MCP Servers   │      │   RAG System    │
       │  (GitHub,      │      │   (pgvector +   │
       │   Azure, etc)  │      │   embeddings)   │
       └────────────────┘      └─────────────────┘
```

---

## 2. Stack tecnologico base

### Backend
- **FastAPI** (Python): API REST + WebSocket
- **PostgreSQL**: Database relazionale + estensione `pgvector` per RAG
- **SQLAlchemy**: ORM async per accesso DB
- **Alembic**: Migrations del database

### Frontend
- **React** + **TypeScript**
- **Vite**: Build tool ultrarapido
- **Tailwind CSS**: Utility-first CSS
- **WebSocket**: Real-time progress streaming

### Orchestrazione AI
- **LangGraph**: Framework per workflow multi-agente
- **LangChain**: Libreria per LLM integration
- **Claude 4.5 Haiku/Sonnet** (Anthropic): Modelli LLM
- **Deep Agents**: Framework per agenti con planning autonomo

### Integrazioni
- **MCP (Model Context Protocol)**: Standard per tool integration
- **GitHub API** (PyGithub): Repository creation/push
- **Azure DevOps API**: Work item management
- **Railway CLI**: Deployment automation

---

## 3. Orchestrazione con LangGraph

### Che cos'è LangGraph?

**LangGraph** è un framework per creare workflow multi-agente usando **grafi stateful**. Ogni nodo del grafo è un agente autonomo che riceve uno stato, esegue un compito, e restituisce uno stato aggiornato.

**Analogia**: LangGraph è come un **assembly line in una fabbrica**:
- Ogni **postazione** = nodo del grafo (agente)
- Il **prodotto** = `OrchestraState` (dizionario che fluisce tra i nodi)
- Il **caposquadra** = LangGraph executor (decide il routing)
- Il **nastro trasportatore** = edges del grafo (collegamenti tra nodi)

### Struttura del grafo

```python
# File: AI_agents/graph/graph.py

START
  ↓
knowledge_retrieval  # Recupera docs da RAG
  ↓
design               # Genera architettura app
  ↓
┌────────┬────────────┬───────────┐
│        │            │           │
backend  frontend  backlog  # Esecuzione PARALLELA
│        │            │
└────────┴────────────┴───────────┘
  ↓
integration_check    # Verifica coerenza
  ↓
  conditional routing (errors? → error_handler : devops_agent)
  ↓
devops_agent         # Genera CI/CD config
  ↓
publish_agent        # Pubblica su GitHub
  ↓
END
```

### OrchestraState: il contratto tra agenti

Il cuore di LangGraph è lo **stato condiviso** che fluisce tra i nodi.

```python
# File: AI_agents/graph/state.py

class OrchestraState(TypedDict):
    # INPUT dall'utente
    requirements: str           # "Create a todo app with auth"
    project_id: str             # Unique ID
    user_id: str
    ai_provider: str            # "anthropic" | "openai"

    # OUTPUT degli agenti
    design_yaml: dict           # Design agent → Backend/Frontend
    api_schema: list            # Architect → Backend
    db_schema: list             # Architect → Backend
    backend_code: dict          # Backend → Publish (files)
    frontend_code: dict         # Frontend → Publish (files)
    devops_config: dict         # DevOps → Publish (CI/CD)

    # SUPPORTING SYSTEMS
    rag_context: list           # Knowledge agent → All agents
    backlog_items: list         # Backlog agent → Project Manager

    # ORCHESTRATION
    current_step: str           # "design", "backend_agent", etc.
    completed_steps: list       # ["design", "backend_agent"]
    agent_statuses: dict        # {"design": "completed"}
    errors: dict                # {"backend_agent": "error msg"}
```

**Analogia dello stato**: `OrchestraState` è come un **plico di documenti** che passa di mano in mano in un ufficio. Ogni impiegato (agente):
1. Legge i documenti ricevuti
2. Aggiunge i suoi contributi
3. Passa il plico aggiornato al collega successivo

### Parallel execution con fan-out

LangGraph supporta l'**esecuzione parallela** di agenti usando `Send` API:

```python
# File: AI_agents/graph/graph.py

def fan_out_to_parallel_agents(state: OrchestraState):
    """Dopo design, lancia 3 agenti in parallelo"""
    return [
        Send("backend_agent", state),
        Send("frontend_agent", state),
        Send("backlog_agent", state),
    ]

# Nel grafo
graph.add_conditional_edges(
    "design",
    fan_out_to_parallel_agents,
    ["backend_agent", "frontend_agent", "backlog_agent"]
)
```

**Vantaggi**:
- ⚡ Velocità: 3x più rapido (backend, frontend, backlog in parallelo)
- 🔒 Sicurezza: Ogni agente legge lo stato ma non interferisce con gli altri
- 📦 Aggregazione: I risultati vengono "mergiati" automaticamente da LangGraph

### Conditional routing

LangGraph permette routing dinamico basato sullo stato:

```python
def route_after_integration_check(state: OrchestraState):
    """Controlla errori e decide il prossimo nodo"""
    has_errors = any(state["errors"].values())

    if has_errors:
        return "error_handler"  # Gestisci errori
    else:
        return "devops_agent"   # Continua pipeline
```

**Analogia**: È come un **filtro qualità** in fabbrica: se il prodotto ha difetti, va in riparazione; altrimenti prosegue verso packaging.

### Checkpointing per human-in-the-loop

LangGraph supporta **checkpoint** per salvare lo stato e permettere review umana:

```python
# File: AI_agents/graph/graph.py

_app = graph_builder.compile(
    checkpointer=AsyncPostgresSaver.from_conn_string(DATABASE_URL),
    interrupt_before=["backend_agent"]  # PAUSA dopo design
)
```

**Workflow con checkpoint**:
1. Utente lancia generazione → LangGraph esegue fino a `design`
2. LangGraph salva checkpoint in DB e si ferma
3. Frontend mostra design → utente approva/modifica
4. Utente clicca "Continue" → LangGraph riprende da checkpoint
5. Backend/Frontend/DevOps/Publish completano il lavoro

**Analogia**: È come un **checkpoint in un videogioco**: puoi salvare, spegnere, e riprendere esattamente da dove eri rimasto.

---

## 4. Sistema MCP (Model Context Protocol)

### Che cos'è MCP?

**Model Context Protocol** è uno standard open-source (creato da Anthropic) che permette agli **LLM di usare tool esterni** in modo standardizzato. È come un'**API universale** per tool integration.

**Analogia**: MCP è come un **set di prese elettriche universali**:
- Ogni **MCP Server** = presa elettrica specifica (GitHub, Azure, Railway)
- Il **client MCP** = adattatore universale che si collega a tutte
- Gli **agenti AI** = dispositivi che usano le prese per fare lavoro

### Architettura MCP in Agentic Orchestra

```
┌──────────────────────────────────────────────────────┐
│                   AGENTE AI                          │
│  "Create a GitHub repo named 'todo-app'"             │
└─────────────────────┬────────────────────────────────┘
                      │ Tool call request
┌─────────────────────▼────────────────────────────────┐
│              MCP CLIENT MANAGER                      │
│  • Connette ai server MCP via stdio                  │
│  • Traduce tool calls in formato MCP                 │
│  • Gestisce autenticazione (token injection)         │
└─────────────────────┬────────────────────────────────┘
                      │ stdio communication
        ┌─────────────┼──────────────┐
        ▼             ▼              ▼
   ┌─────────┐  ┌──────────┐  ┌─────────┐
   │ GitHub  │  │  Azure   │  │ Railway │
   │  MCP    │  │ DevOps   │  │  MCP    │
   │ Server  │  │   MCP    │  │ Server  │
   └─────────┘  └──────────┘  └─────────┘
        │             │              │
        ▼             ▼              ▼
   GitHub API   Azure API    Railway CLI
```

### Implementazione MCP Server (esempio GitHub)

**File**: `mcp_servers/github_server.py`

```python
from mcp.server import Server
from mcp.types import Tool, TextContent
from github import Github

# 1. Inizializza MCP Server
app = Server("github-server")

# 2. Definisci tool disponibili
@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="create_repository",
            description="Create a new GitHub repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "private": {"type": "boolean"},
                    "description": {"type": "string"}
                },
                "required": ["name"]
            }
        ),
        Tool(name="push_files", ...),
        Tool(name="create_pull_request", ...),
    ]

# 3. Implementa esecuzione tool
@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "create_repository":
        # Legge token da env var (iniettato dall'orchestratore)
        token = os.getenv("GITHUB_TOKEN")
        client = Github(token)

        # Crea repository
        user = client.get_user()
        repo = user.create_repo(
            name=arguments["name"],
            private=arguments.get("private", False),
            description=arguments.get("description", "")
        )

        return {"url": repo.html_url, "name": repo.name}
```

**Caratteristiche chiave**:
- ✅ **Standardizzazione**: Schema JSON per input/output
- 🔐 **Sicurezza**: Token letto da env var (mai hardcoded)
- 📝 **Logging**: Tracciabilità completa (`@log_tool_call` decorator)
- 🛡️ **Error handling**: Errori standardizzati (`MCPAuthError`, `format_error_response`)

### MCP Client Manager

**File**: `mcp_servers/client.py`

```python
class MCPClientManager:
    """Gestisce connessioni a MCP servers"""

    # Configurazione server disponibili
    SERVERS = {
        "github": {
            "command": "python",
            "args": ["-m", "mcp_servers.github_server"],
            "description": "GitHub integration"
        },
        "azuredevops": {...},
        "deploy": {...}
    }

    async def connect(self, server_name: str):
        """Connette a un server MCP via stdio"""
        server_params = StdioServerParameters(
            command=self.SERVERS[server_name]["command"],
            args=self.SERVERS[server_name]["args"],
            env=None  # Eredita env vars (include token iniettati)
        )

        async with stdio_client(server_params) as (read, write):
            client = ClientSession(read, write)
            await client.initialize()
            self._clients[server_name] = client

    async def call_tool(self, server: str, tool_name: str, args: dict):
        """Esegue un tool su un server specifico"""
        client = self._clients[server]
        result = await client.call_tool(tool_name, args)
        return result
```

### Token injection flow

**Come funziona l'autenticazione?**

1. **Utente connette account** (UI):
   ```
   User → AuthScreen → POST /auth/github → DB salva token criptato
   ```

2. **Orchestratore inietta token** (prima di LangGraph):
   ```python
   # File: orchestrator-ui/backend/orchestrator.py

   def _inject_env_vars(self, db: Session, user_id: int):
       """Inietta token come env vars"""
       user = db.query(User).filter(User.id == user_id).first()

       if user.github_token:
           os.environ["GITHUB_TOKEN"] = user.github_token

       # Azure DevOps, Railway, etc. (da DeployProviderAuth)
       # ...
   ```

3. **MCP Server legge token**:
   ```python
   def get_github_client() -> Github:
       token = inject_token("GITHUB_TOKEN")  # Raise se mancante
       return Github(token)
   ```

**Analogia**: È come un **badge aziendale**:
- L'utente registra la badge una volta (UI)
- La guardia (orchestratore) verifica e ti dà accesso
- Ogni porta (MCP server) riconosce il badge automaticamente

### Esempio di uso in un agente

**File**: `AI_agents/graph/nodes/publish_node.py`

```python
async def publish_node(state: OrchestraState):
    """Pubblica app su GitHub usando Deep Agents + MCP"""

    # 1. Carica tool GitHub da MCP
    mcp = MCPClientManager()
    github_tools = await mcp.get_tools(["github"])

    # 2. Crea Deep Agent con GitHub tools
    agent = create_deep_agent(
        model=llm,
        tools=github_tools,  # Tool MCP disponibili
        system_prompt="You publish code to GitHub..."
    )

    # 3. Agente decide autonomamente quali tool usare
    result = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": f"Create repo '{app_name}' and push files"
        }]
    })

    # 4. Deep Agent chiama automaticamente:
    #    - create_repository(name="todo-app")
    #    - push_files(repo="user/todo-app", files=[...])

    return state
```

**Flusso completo**:
```
Agente: "Devo pubblicare su GitHub"
  ↓
Deep Agent riceve tools=github_tools
  ↓
LLM decide: "Serve create_repository tool"
  ↓
Tool call → MCPClientManager.call_tool("github", "create_repository", {...})
  ↓
MCP Client → stdio → GitHub MCP Server
  ↓
GitHub MCP Server → PyGithub → GitHub API
  ↓
Risultato: {"url": "https://github.com/user/todo-app"}
```

---

## 5. Sistema RAG (Retrieval-Augmented Generation)

### Che cos'è il RAG?

**RAG** (Retrieval-Augmented Generation) è una tecnica che **aumenta le capacità dell'LLM** fornendo documentazione/esempi rilevanti al contesto della richiesta.

**Analogia**: Il RAG è come un **assistente bibliotecario**:
- L'**LLM** = programmatore esperto ma con memoria limitata
- Il **RAG** = bibliotecario che cerca manuali/esempi pertinenti
- La **vector store** = biblioteca indicizzata semanticamente
- La **query** = "Ho bisogno di esempi di autenticazione JWT in .NET"

### Architettura RAG in Agentic Orchestra

```
┌─────────────────────────────────────────────────────┐
│            KNOWLEDGE AGENT                          │
│  1. Riceve requirements utente                      │
│  2. Cerca in vector store documenti rilevanti       │
│  3. Se insufficienti → fetch da sources             │
│  4. Restituisce top-K docs in state["rag_context"]  │
└────────────┬────────────────────────────────────────┘
             │
     ┌───────▼─────────┐
     │  VECTOR STORE   │
     │   (pgvector)    │
     │                 │
     │  • Embeddings   │
     │  • Cosine sim   │
     │  • Deduplication│
     └───────┬─────────┘
             │
    ┌────────▼─────────┐
    │ KNOWLEDGE SOURCES│
    │                  │
    │ • GitHub Repos   │
    │ • Confluence     │
    │ • Stack Overflow │
    │ • Docs sites     │
    └──────────────────┘
```

### Componenti del sistema RAG

#### 1. Vector Store Service

**File**: `AI_agents/knowledge/vector_store.py`

```python
class VectorStoreService:
    """Gestisce embeddings e semantic search con pgvector"""

    def __init__(self):
        # Modello multilingua da HuggingFace
        self.embedding_model = SentenceTransformer(
            "paraphrase-multilingual-mpnet-base-v2"
        )
        self.embedding_dim = 768  # Dimensione vettore

    async def upsert(self, source_name: str, documents: list):
        """Inserisce documenti con deduplicazione"""
        # 1. Genera embeddings per tutti i documenti
        embeddings = self.embedding_model.encode(
            [doc.content for doc in documents]
        )

        # 2. Calcola hash per deduplicazione
        for doc, embedding in zip(documents, embeddings):
            content_hash = hashlib.sha256(doc.content.encode()).hexdigest()

            # 3. Insert con ON CONFLICT (content_hash) DO NOTHING
            await conn.execute("""
                INSERT INTO knowledge_embeddings
                (content, source, metadata, content_hash, embedding)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (content_hash) DO NOTHING
            """, doc.content, source_name, doc.metadata,
                 content_hash, embedding.tolist())

    async def search(self, query: str, top_k: int = 5):
        """Semantic search con cosine similarity"""
        # 1. Genera embedding della query
        query_embedding = self.embedding_model.encode(query)

        # 2. Cerca usando operatore <=> (cosine distance)
        rows = await conn.fetch("""
            SELECT content, source, metadata,
                   (1 - (embedding <=> $1)) AS similarity
            FROM knowledge_embeddings
            ORDER BY embedding <=> $1
            LIMIT $2
        """, query_embedding.tolist(), top_k)

        return [Document(**row) for row in rows]
```

**Tecnologie chiave**:
- **pgvector**: Estensione PostgreSQL per vettori (tipo `vector(768)`)
- **ivfflat index**: Indice per ricerca rapida (100 liste)
- **Sentence Transformers**: Modelli di embedding (768 dimensioni)
- **Cosine similarity**: Misura vicinanza semantica (0-1)

#### 2. Knowledge Agent

**File**: `AI_agents/knowledge/knowledge_agent.py`

```python
class KnowledgeAgent:
    """Orchestrate RAG retrieval"""

    async def run(self, state: OrchestraState):
        # 1. Costruisci query dai requirements
        query = self._build_search_query(state)
        # "Create todo app with React and JWT auth"

        # 2. Cerca in vector store
        docs = await self.vector_store.search(query, top_k=5)

        # 3. Se insufficienti, fetch da sources
        if len(docs) < 3:
            await self._fetch_and_index_sources(query)
            docs = await self.vector_store.search(query, top_k=5)

        # 4. Formatta per RAG context
        state["rag_context"] = [
            {
                "content": doc.content,
                "source": doc.source,
                "metadata": doc.metadata
            }
            for doc in docs
        ]

        return state
```

#### 3. Knowledge Sources (estensibili)

**File**: `AI_agents/knowledge/sources/github_source.py` (esempio)

```python
class GitHubKnowledgeSource(KnowledgeSource):
    """Fetches code examples from GitHub repositories"""

    async def fetch(self, query: str) -> list[Document]:
        # 1. Cerca repository rilevanti
        repos = self.github.search_repositories(
            query=f"{query} stars:>100",
            sort="stars"
        )

        # 2. Estrai README e file rilevanti
        documents = []
        for repo in repos[:5]:  # Top 5 repos
            readme = repo.get_readme()
            documents.append(Document(
                content=readme.decoded_content.decode("utf-8"),
                source=f"github:{repo.full_name}",
                metadata={"stars": repo.stargazers_count}
            ))

        return documents
```

**Altri sources disponibili**:
- `ConfluenceSource`: Documentazione aziendale
- `StackOverflowSource`: Q&A pertinenti
- `DocsiteSource`: Documentazione framework (React Docs, .NET Docs)

### Flusso RAG completo: esempio

**Scenario**: Utente richiede "Todo app con autenticazione JWT"

1. **Knowledge Agent riceve requirements**:
   ```python
   state["requirements"] = "Todo app with JWT auth and React"
   ```

2. **Genera query di ricerca**:
   ```python
   query = "Todo app with JWT auth and React"
   ```

3. **Cerca in vector store**:
   ```sql
   -- Query effettiva eseguita
   SELECT content, source, (1 - (embedding <=> embedding_query)) AS similarity
   FROM knowledge_embeddings
   ORDER BY embedding <=> embedding_query
   LIMIT 5
   ```

4. **Risultati (esempio)**:
   ```
   [
     {
       "content": "# JWT Authentication in ASP.NET Core\n\n```csharp\nservices.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)...",
       "source": "github:dotnet/aspnetcore",
       "similarity": 0.89
     },
     {
       "content": "# React Todo App with JWT\n\n```jsx\nconst login = async () => {\n  const token = await fetchToken()...",
       "source": "github:facebook/react",
       "similarity": 0.85
     },
     ...
   ]
   ```

5. **Knowledge Agent popola state**:
   ```python
   state["rag_context"] = [
     "[Document 1 - Source: github:dotnet/aspnetcore]\n# JWT Authentication...",
     "[Document 2 - Source: github:facebook/react]\n# React Todo App...",
     ...
   ]
   ```

6. **Design Agent usa RAG context**:
   ```python
   prompt = f"""
   Requirements: {state["requirements"]}

   Relevant documentation:
   {state["rag_context"]}

   Generate application design following best practices from above docs.
   """

   result = await llm.ainvoke(prompt)
   ```

**Risultato**: Il Design Agent genera architettura usando pattern **reali** da progetti open-source, non solo conoscenza teorica dell'LLM!

---

## 6. Architettura degli agenti

### Tipologie di agenti

Agentic Orchestra usa **tre tipi di agenti** a seconda della complessità del compito:

#### 1. **Deep Agents** (con planning autonomo)

**Quando usarli**: Compiti multi-step che richiedono decisioni dinamiche

**Esempio**: Design Agent, Publish Agent

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model=llm,
    tools=[...],  # Tool MCP disponibili
    system_prompt="You are an architect..."
)

# Deep Agent pianifica automaticamente:
# 1. Parse requirements
# 2. Identify entities
# 3. Design API schema
# 4. Validate completeness
result = await agent.ainvoke({"messages": [...]})
```

**Caratteristiche**:
- ✅ **Planning automatico**: usa `write_todos` tool per pianificare step
- ✅ **Tool use dinamico**: decide quali tool usare e quando
- ✅ **Error recovery**: retry automatico se fallisce

**Analogia**: Deep Agent è un **project manager esperto** che:
- Riceve un obiettivo ("Design an app")
- Pianifica i task ("1. Parse, 2. Design, 3. Validate")
- Esegue autonomamente usando tool
- Verifica il risultato

#### 2. **Base Agents** (single-shot generation)

**Quando usarli**: Compiti ben definiti con input/output prevedibili

**Esempio**: Backend Agent, Frontend Agent, DevOps Agent

```python
class BaseAgent:
    """Agent semplice per generazione codice"""

    async def run(self, state: OrchestraState):
        # 1. Estrai input da state
        design = state["design_yaml"]
        api_schema = state["api_schema"]

        # 2. Costruisci prompt
        prompt = self._build_prompt(design, api_schema)

        # 3. Single LLM call
        result = await self.llm.ainvoke(prompt)

        # 4. Parse e restituisci
        state["backend_code"] = self._parse_code(result)
        return state
```

**Caratteristiche**:
- ⚡ **Velocità**: Single LLM call, no planning overhead
- 🎯 **Semplicità**: Input → LLM → Output
- 💰 **Costo ridotto**: Meno token consumati

#### 3. **Knowledge Agent** (RAG orchestrator)

**Specializzato**: Recupero contestuale da vector store + sources

Vedi [sezione RAG](#5-sistema-rag-retrieval-augmented-generation)

### Pattern di implementazione degli agenti

Ogni agente node segue questo pattern:

```python
# File: AI_agents/graph/nodes/example_node.py

async def example_node(state: OrchestraState) -> OrchestraState:
    """
    Example agent node.

    Input:
        state["requirements"]
        state["rag_context"]

    Output:
        state["example_output"]

    Error Handling:
        Sets state["errors"]["example_node"] on failure
    """
    logger.info("[example_node] Starting...")

    # 1. Update orchestration state
    state["current_step"] = "example_node"
    state["agent_statuses"]["example_node"] = AgentStatus.RUNNING

    try:
        # 2. Extract input
        requirements = state.get("requirements", "")
        if not requirements:
            raise ValueError("Missing requirements")

        # 3. Get LLM client (NEVER instantiate directly!)
        provider = state.get("ai_provider", "anthropic")
        llm = get_llm_client(provider, {"temperature": 0.1})

        # 4. Execute agent logic
        result = await execute_agent_work(llm, requirements)

        # 5. Populate state
        state["example_output"] = result

        # 6. Mark success
        state["completed_steps"].append("example_node")
        state["agent_statuses"]["example_node"] = AgentStatus.COMPLETED

    except Exception as e:
        logger.error(f"[example_node] Failed: {e}")

        # NEVER raise - set error in state
        state["errors"]["example_node"] = str(e)
        state["agent_statuses"]["example_node"] = AgentStatus.FAILED

    return state
```

**Regole chiave**:
1. ✅ **Sempre async**: `async def node(state) -> state`
2. ✅ **Update status**: `state["current_step"]`, `state["agent_statuses"]`
3. ✅ **Use LLM factory**: `get_llm_client()` (mai istanziare diretto)
4. ✅ **Error in state**: `state["errors"][node_name]` (mai raise)
5. ✅ **Return state**: Sempre restituire `OrchestraState` aggiornato

---

## 7. Flusso completo di generazione

### Step-by-step: dalla richiesta al deploy

#### **STEP 0: Utente invia richiesta**

**Frontend** → **POST /api/generations/start**

```typescript
// File: orchestrator-ui/frontend/src/screens/MVPCreationScreen.tsx

const handleGenerate = async () => {
  const ws = new WebSocket(`ws://localhost:8000/ws/${generationId}`);

  const response = await fetch("/api/generations/start", {
    method: "POST",
    body: JSON.stringify({
      mvp_description: "Todo app with JWT auth",
      features: ["User login", "CRUD todos", "Dark mode"],
      tech_stack: {
        backend: "ASP.NET Core",
        frontend: "React",
        database: "PostgreSQL",
        deploy_platform: "Railway"
      }
    })
  });

  // Riceve progress via WebSocket
  ws.onmessage = (event) => {
    const progress = JSON.parse(event.data);
    setProgress(progress.percentage);
  };
};
```

#### **STEP 1: Orchestratore prepara l'esecuzione**

**File**: `orchestrator-ui/backend/orchestrator.py`

```python
async def run_generation(generation_id, request, db, user_id):
    # 1. Crea record progetto in DB
    project = crud.create_project(
        db=db,
        name=f"Generated App - {generation_id[:8]}",
        status="in_progress"
    )

    # 2. Inietta token/config come env vars
    self._inject_env_vars(db, user_id)
    # → os.environ["GITHUB_TOKEN"] = user.github_token
    # → os.environ["ADESSO_AI_HUB_KEY"] = decrypt(config.ai_api_key)

    # 3. Costruisci initial state
    state = self._build_initial_state(request, project.id, user_id)

    # 4. Avvia LangGraph execution
    async for event in langgraph_app.astream(state):
        # 5. Broadcast progress via WebSocket
        step_info = self._map_event_to_step_info(event)
        if step_info:
            await manager.broadcast(generation_id, {
                "type": "progress",
                "step": step_info["step"],
                "percentage": step_info["percentage"]
            })
```

#### **STEP 2: LangGraph esegue il grafo**

```python
# Execution flow
START
  ↓
knowledge_retrieval(state)  # RAG: cerca docs rilevanti
  ↓
  state["rag_context"] = [docs...]
  ↓
design_node(state)          # Deep Agent: genera architettura
  ↓
  state["design_yaml"] = {...}
  state["api_schema"] = [...]
  state["db_schema"] = [...]
  ↓
fan_out_to_parallel_agents(state)
  ↓
  ┌────────────────┬─────────────────┬────────────────┐
  │                │                 │                │
backend_node    frontend_node    backlog_node
  │                │                 │
  state["backend_code"] = {...}
                   state["frontend_code"] = {...}
                                     state["backlog_items"] = [...]
  │                │                 │
  └────────────────┴─────────────────┴────────────────┘
  ↓
integration_check(state)    # Verifica coerenza
  ↓
  conditional: errors? → error_handler : devops_agent
  ↓
devops_node(state)          # Genera CI/CD config
  ↓
  state["devops_config"] = {...}
  ↓
publish_node(state)         # Deep Agent: pubblica su GitHub
  ↓
  state["github_repo_url"] = "https://github.com/..."
  ↓
END
```

#### **STEP 3: Knowledge Retrieval (RAG)**

```python
# knowledge_retrieval node
query = "Todo app with JWT auth and React"

# Cerca in pgvector
docs = await vector_store.search(query, top_k=5)
# → Returns [
#     {content: "JWT in ASP.NET...", source: "github:dotnet/aspnetcore"},
#     {content: "React auth...", source: "github:facebook/react"},
#     ...
#   ]

# Se insufficienti, fetch da sources
if len(docs) < 3:
    github_docs = await github_source.fetch(query)
    await vector_store.upsert("github", github_docs)
    docs = await vector_store.search(query, top_k=5)

state["rag_context"] = docs
```

#### **STEP 4: Design Generation (Deep Agent)**

```python
# design_node con Deep Agents
agent = create_deep_agent(
    model=llm,
    tools=[],
    system_prompt="You are a .NET/React architect..."
)

message = f"""
Requirements: {state["requirements"]}

Relevant docs:
{state["rag_context"]}

Produce JSON with: app_name, stack, entities, api_endpoints...
"""

result = await agent.ainvoke({"messages": [{"role": "user", "content": message}]})

# Deep Agent pianifica internamente:
# 1. Parse requirements → entities: User, Todo
# 2. Design stack → ASP.NET + React + PostgreSQL
# 3. API schema → GET /todos, POST /todos, etc.
# 4. Validate → all CRUD ops covered

state["design_yaml"] = {
    "app_name": "todo-app",
    "stack": {"backend": "ASP.NET Core", "frontend": "React"},
    "entities": [
        {"name": "User", "fields": [{"name": "email", "type": "string"}]},
        {"name": "Todo", "fields": [{"name": "title", "type": "string"}]}
    ],
    "api_endpoints": [
        {"method": "POST", "path": "/auth/login"},
        {"method": "GET", "path": "/todos"},
        {"method": "POST", "path": "/todos"}
    ]
}
```

#### **STEP 5: Parallel Code Generation**

Tre agenti eseguono **in parallelo**:

```python
# backend_node (Base Agent)
state["backend_code"] = {
    "Program.cs": "var builder = WebApplication.CreateBuilder()...",
    "Models/User.cs": "public class User { ... }",
    "Services/AuthService.cs": "public class AuthService { ... }",
    "Controllers/TodoController.cs": "..."
}

# frontend_node (Base Agent)
state["frontend_code"] = {
    "src/App.tsx": "export default function App() { ... }",
    "src/components/TodoList.tsx": "...",
    "src/services/api.ts": "export const fetchTodos = () => { ... }"
}

# backlog_node (Base Agent)
state["backlog_items"] = [
    {"title": "Implement user login", "priority": "high"},
    {"title": "Add dark mode toggle", "priority": "medium"}
]
```

#### **STEP 6: Integration Check**

```python
# integration_check node
errors = []

# Verifica che backend esponga tutti gli endpoint del design
for endpoint in state["api_schema"]:
    if endpoint["path"] not in state["backend_code"]["Controllers/..."]:
        errors.append(f"Missing endpoint: {endpoint['path']}")

# Verifica che frontend chiami gli endpoint corretti
for file in state["frontend_code"].values():
    if "fetch('/wrong-path')" in file:
        errors.append("Frontend calls non-existent endpoint")

if errors:
    state["errors"]["integration_check"] = "; ".join(errors)
    # → Routing: integration_check → error_handler
else:
    # → Routing: integration_check → devops_agent
    pass
```

#### **STEP 7: DevOps Configuration**

```python
# devops_node (Base Agent)
state["devops_config"] = {
    ".github/workflows/ci.yml": """
        name: CI
        on: [push]
        jobs:
          build:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v2
              - name: Build backend
                run: dotnet build
              - name: Run tests
                run: dotnet test
    """,
    "Dockerfile": """
        FROM mcr.microsoft.com/dotnet/aspnet:8.0
        WORKDIR /app
        COPY . .
        ENTRYPOINT ["dotnet", "TodoApp.dll"]
    """,
    "docker-compose.yml": "..."
}
```

#### **STEP 8: GitHub Publishing (Deep Agent + MCP)**

```python
# publish_node
mcp = MCPClientManager()
github_tools = await mcp.get_tools(["github"])

agent = create_deep_agent(
    model=llm,
    tools=github_tools,
    system_prompt="You publish code to GitHub..."
)

message = f"""
Publish app '{state["design_yaml"]["app_name"]}' to GitHub:
1. Create repo
2. Push all files from state["backend_code"], state["frontend_code"], state["devops_config"]
"""

result = await agent.ainvoke({"messages": [{"role": "user", "content": message}]})

# Deep Agent esegue automaticamente:
# 1. Tool call: create_repository(name="todo-app")
#    → MCP GitHub Server → GitHub API
#    → Result: {"url": "https://github.com/user/todo-app"}
#
# 2. Tool call: push_files(
#      repo="user/todo-app",
#      files=[
#        {"path": "Program.cs", "content": "..."},
#        {"path": "src/App.tsx", "content": "..."},
#        ...
#      ]
#    )
#    → MCP GitHub Server → GitHub API
#    → Result: {"commit_sha": "abc123"}

state["github_repo_url"] = "https://github.com/user/todo-app"
```

#### **STEP 9: Completamento e notifica**

```python
# orchestrator.py - dopo LangGraph execution
crud.update_project_status(db, project.id, "completed")

await manager.broadcast(generation_id, {
    "type": "progress",
    "step": "complete",
    "percentage": 100,
    "message": "App generated successfully!",
    "github_url": state["github_repo_url"]
})

# Frontend riceve WebSocket message e mostra:
# ✅ Generation complete!
# 🔗 Repository: https://github.com/user/todo-app
```

---

## 8. Esempio pratico end-to-end

### Scenario: "Genera un'app di gestione spese"

#### Input utente (UI)

```
MVP Description:
"App per tracciare spese personali con grafici mensili"

Features:
- Login con email/password
- Aggiungi/modifica/elimina spese
- Categorizza spese (cibo, trasporti, etc.)
- Visualizza grafici spese per categoria
- Export CSV mensile

Tech Stack:
- Backend: ASP.NET Core
- Frontend: React + TypeScript
- Database: PostgreSQL
- Deploy: Railway
```

#### Processing flow

**1. Knowledge Retrieval (RAG)**

```python
# Query generata
query = "expense tracking app charts CSV export ASP.NET React"

# Vector search results
[
  {
    "content": "# Chart.js in React\n```tsx\nimport { Line } from 'react-chartjs-2'...",
    "source": "github:chartjs/react-chartjs-2",
    "similarity": 0.91
  },
  {
    "content": "# CSV Export in C#\n```csharp\npublic byte[] ExportToCsv(List<Expense> expenses)...",
    "source": "github:joshclose/CsvHelper",
    "similarity": 0.87
  },
  {
    "content": "# ASP.NET Core Entity Framework\n```csharp\npublic class AppDbContext : DbContext...",
    "source": "docs.microsoft.com/ef-core",
    "similarity": 0.85
  }
]
```

**2. Design Generation**

```json
{
  "app_name": "expense-tracker",
  "description": "Personal expense tracking app with monthly charts and CSV export",
  "stack": {
    "backend_framework": "ASP.NET Core 8.0",
    "frontend_framework": "React 18 + TypeScript",
    "database": "PostgreSQL 16",
    "auth_method": "JWT Bearer",
    "charts_library": "Chart.js"
  },
  "entities": [
    {
      "name": "User",
      "fields": [
        {"name": "Id", "type": "Guid", "required": true},
        {"name": "Email", "type": "string", "required": true},
        {"name": "PasswordHash", "type": "string", "required": true}
      ]
    },
    {
      "name": "Expense",
      "fields": [
        {"name": "Id", "type": "Guid", "required": true},
        {"name": "UserId", "type": "Guid", "required": true},
        {"name": "Amount", "type": "decimal", "required": true},
        {"name": "Category", "type": "string", "required": true},
        {"name": "Description", "type": "string", "required": false},
        {"name": "Date", "type": "DateTime", "required": true}
      ]
    }
  ],
  "api_endpoints": [
    {"method": "POST", "path": "/auth/register", "description": "Register new user"},
    {"method": "POST", "path": "/auth/login", "description": "Login and get JWT"},
    {"method": "GET", "path": "/expenses", "description": "Get user's expenses"},
    {"method": "POST", "path": "/expenses", "description": "Create expense"},
    {"method": "PUT", "path": "/expenses/{id}", "description": "Update expense"},
    {"method": "DELETE", "path": "/expenses/{id}", "description": "Delete expense"},
    {"method": "GET", "path": "/expenses/stats", "description": "Get monthly stats by category"},
    {"method": "GET", "path": "/expenses/export", "description": "Export CSV"}
  ],
  "deployment_target": "Railway"
}
```

**3. Backend Generation**

```csharp
// Generated: backend/Models/Expense.cs
public class Expense
{
    public Guid Id { get; set; }
    public Guid UserId { get; set; }
    public decimal Amount { get; set; }
    public string Category { get; set; } = string.Empty;
    public string? Description { get; set; }
    public DateTime Date { get; set; }

    public User User { get; set; } = null!;
}

// Generated: backend/Controllers/ExpenseController.cs
[ApiController]
[Route("api/expenses")]
[Authorize] // JWT authentication
public class ExpenseController : ControllerBase
{
    private readonly IExpenseService _expenseService;

    [HttpGet]
    public async Task<IActionResult> GetExpenses()
    {
        var userId = Guid.Parse(User.FindFirst(ClaimTypes.NameIdentifier)!.Value);
        var expenses = await _expenseService.GetUserExpenses(userId);
        return Ok(expenses);
    }

    [HttpGet("stats")]
    public async Task<IActionResult> GetStats([FromQuery] int month, [FromQuery] int year)
    {
        var userId = Guid.Parse(User.FindFirst(ClaimTypes.NameIdentifier)!.Value);
        var stats = await _expenseService.GetMonthlyStats(userId, month, year);
        return Ok(stats);
    }

    [HttpGet("export")]
    public async Task<IActionResult> ExportCsv([FromQuery] int month, [FromQuery] int year)
    {
        var userId = Guid.Parse(User.FindFirst(ClaimTypes.NameIdentifier)!.Value);
        var csv = await _expenseService.ExportToCsv(userId, month, year);
        return File(csv, "text/csv", $"expenses-{month}-{year}.csv");
    }
}

// Generated: backend/Services/ExpenseService.cs
public class ExpenseService : IExpenseService
{
    public async Task<byte[]> ExportToCsv(Guid userId, int month, int year)
    {
        // Using CsvHelper library (from RAG context!)
        var expenses = await GetUserExpenses(userId, month, year);

        using var memoryStream = new MemoryStream();
        using var writer = new StreamWriter(memoryStream);
        using var csv = new CsvWriter(writer, CultureInfo.InvariantCulture);

        csv.WriteRecords(expenses);
        writer.Flush();
        return memoryStream.ToArray();
    }
}
```

**4. Frontend Generation**

```tsx
// Generated: frontend/src/App.tsx
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement);

export default function App() {
  const [expenses, setExpenses] = useState([]);
  const [stats, setStats] = useState({});

  const chartData = {
    labels: Object.keys(stats), // ['Food', 'Transport', ...]
    datasets: [{
      label: 'Monthly Expenses by Category',
      data: Object.values(stats), // [450, 200, ...]
      borderColor: 'rgb(75, 192, 192)'
    }]
  };

  return (
    <div className="container">
      <ExpenseForm onAdd={addExpense} />
      <ExpenseList expenses={expenses} />
      <Line data={chartData} />
      <button onClick={exportCsv}>Export CSV</button>
    </div>
  );
}

// Generated: frontend/src/services/api.ts
export const fetchStats = async (month: number, year: number) => {
  const response = await fetch(`/api/expenses/stats?month=${month}&year=${year}`, {
    headers: { 'Authorization': `Bearer ${getToken()}` }
  });
  return response.json();
};

export const exportCsv = async () => {
  const response = await fetch('/api/expenses/export?month=11&year=2024', {
    headers: { 'Authorization': `Bearer ${getToken()}` }
  });
  const blob = await response.blob();
  downloadFile(blob, 'expenses.csv');
};
```

**5. DevOps Configuration**

```yaml
# Generated: .github/workflows/ci.yml
name: CI/CD Pipeline
on:
  push:
    branches: [main]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup .NET
        uses: actions/setup-dotnet@v3
        with:
          dotnet-version: '8.0'
      - name: Test
        run: dotnet test backend/

  frontend-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
        working-directory: frontend
      - run: npm run build
        working-directory: frontend
```

```dockerfile
# Generated: Dockerfile
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
WORKDIR /app
EXPOSE 80

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
COPY backend/ .
RUN dotnet restore
RUN dotnet publish -c Release -o /app/publish

FROM base AS final
COPY --from=build /app/publish .
ENTRYPOINT ["dotnet", "ExpenseTracker.dll"]
```

**6. GitHub Publishing**

```python
# Deep Agent executes:
# 1. create_repository(name="expense-tracker", private=False)
#    → Result: https://github.com/user/expense-tracker

# 2. push_files(
#      repo="user/expense-tracker",
#      files=[
#        {"path": "backend/Program.cs", "content": "..."},
#        {"path": "backend/Models/Expense.cs", "content": "..."},
#        {"path": "frontend/src/App.tsx", "content": "..."},
#        {"path": ".github/workflows/ci.yml", "content": "..."},
#        {"path": "Dockerfile", "content": "..."},
#        {"path": "README.md", "content": "# Expense Tracker\n\n..."}
#      ],
#      message="Initial commit - Generated by Agentic Orchestra"
#    )
#    → Result: commit SHA abc123def
```

#### Output finale

**Repository creato**: `https://github.com/user/expense-tracker`

**Struttura**:
```
expense-tracker/
├── backend/
│   ├── Program.cs
│   ├── Models/
│   │   ├── User.cs
│   │   └── Expense.cs
│   ├── Controllers/
│   │   ├── AuthController.cs
│   │   └── ExpenseController.cs
│   ├── Services/
│   │   └── ExpenseService.cs
│   └── appsettings.json
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── ExpenseForm.tsx
│   │   │   └── ExpenseList.tsx
│   │   └── services/
│   │       └── api.ts
│   ├── package.json
│   └── vite.config.ts
├── .github/
│   └── workflows/
│       └── ci.yml
├── Dockerfile
├── docker-compose.yml
└── README.md
```

**Tempo totale**: ~3-5 minuti (dipende da complessità e parallelizzazione)

---

## 🎓 Conclusioni e best practices

### Vantaggi dell'architettura

1. **Modularità**: Ogni agente è indipendente e testabile
2. **Scalabilità**: Aggiungere nuovi agenti è semplice (nuovo file in `nodes/`)
3. **Parallelismo**: Backend/Frontend/Backlog eseguono simultaneamente
4. **Estensibilità**: Nuovi MCP server = nuove integrazioni (Azure, AWS, etc.)
5. **Qualità**: RAG assicura best practices da progetti reali
6. **Trasparenza**: WebSocket streaming mostra progress in real-time
7. **Recovery**: Checkpoint LangGraph permettono human-in-the-loop

### Tecnologie chiave da studiare

1. **LangGraph**: [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph)
2. **MCP**: [modelcontextprotocol.io](https://modelcontextprotocol.io)
3. **Deep Agents**: Framework custom per planning autonomo
4. **pgvector**: [pgvector/pgvector](https://github.com/pgvector/pgvector)
5. **Sentence Transformers**: [sbert.net](https://www.sbert.net)

### Pattern architetturali applicati

- **Orchestration Pattern**: LangGraph coordina agenti
- **State Management**: `OrchestraState` TypedDict immutabile
- **Pub/Sub**: WebSocket per real-time updates
- **RAG Pattern**: Vector search + LLM generation
- **Tool Use Pattern**: MCP standard per integrazioni
- **Circuit Breaker**: Error handling con routing condizionale
- **Checkpointing**: Stateful workflow con human approval

### Prossimi sviluppi

- [ ] **Multi-tenant**: Supporto per team/organizzazioni
- [ ] **Agent marketplace**: Agenti community-contributed
- [ ] **Advanced RAG**: Hybrid search (keyword + semantic)
- [ ] **Cost optimization**: Token usage tracking & budgeting
- [ ] **A/B testing**: Confronto output tra diversi modelli LLM

---

## 📚 Riferimenti

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Model Context Protocol Spec](https://spec.modelcontextprotocol.io)
- [Anthropic Claude API](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [pgvector PostgreSQL Extension](https://github.com/pgvector/pgvector)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React + TypeScript](https://react.dev/learn/typescript)

---

**Autore**: Agentic Orchestra Team
**Ultimo aggiornamento**: 2026-04-11
**Versione**: 1.0
