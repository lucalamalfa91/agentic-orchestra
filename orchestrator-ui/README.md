# Orchestrator UI

Web-based user interface for managing AI app generation with the Agentic Orchestra.

## Overview

The Orchestrator UI provides a visual interface for the AI Factory, allowing users to:

- **Configure app requirements** through a web form (no manual file editing)
- **Monitor real-time progress** during generation (6-step visual progress bar)
- **View project history** with links to generated GitHub repositories
- **Edit and regenerate** existing projects

## Architecture

```
orchestrator-ui/
├── backend/                 # FastAPI REST + WebSocket server
│   ├── main.py             # FastAPI app entry point
│   ├── database.py         # SQLAlchemy configuration
│   ├── models.py           # Database ORM models
│   ├── schemas.py          # Pydantic validation schemas
│   ├── crud.py             # Database CRUD operations
│   ├── websocket.py        # WebSocket connection manager
│   ├── orchestrator.py     # Subprocess wrapper for run_all_agents.py
│   ├── api/
│   │   ├── projects.py     # Projects REST endpoints
│   │   └── generation.py   # Generation REST endpoints
│   └── init_db.py          # Database initialization script
└── frontend/                # React + TypeScript + Tailwind UI
    ├── src/
    │   ├── App.tsx         # Main application component
    │   ├── components/     # React components
    │   │   ├── GenerationForm.tsx
    │   │   ├── ProgressIndicator.tsx
    │   │   ├── ProjectCard.tsx
    │   │   └── ProjectHistory.tsx
    │   ├── hooks/          # Custom React hooks
    │   │   ├── useWebSocket.ts
    │   │   └── useGeneration.ts
    │   ├── api/            # API client
    │   │   └── client.ts
    │   └── types/          # TypeScript types
    │       └── index.ts
    └── package.json
```

## Database Schema

The UI uses SQLite to store:

- **Projects**: Generated app metadata (name, description, GitHub URL, status)
- **Project Requirements**: Original requirements for regeneration
- **Generation Logs**: Execution logs for debugging

```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    github_repo_url VARCHAR(500),
    status VARCHAR(50),
    created_at TIMESTAMP
);

CREATE TABLE project_requirements (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    mvp_description TEXT,
    features TEXT,  -- JSON array
    user_stories TEXT,  -- JSON array
    frontend_framework VARCHAR(50),
    backend_framework VARCHAR(50),
    database_type VARCHAR(50),
    deploy_platform VARCHAR(50),
    requirements_text TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE generation_logs (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    step_name VARCHAR(100),
    status VARCHAR(50),
    message TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

## API Documentation

### REST Endpoints

**Projects**
- `GET /api/projects/` - List all projects (paginated)
- `GET /api/projects/{id}` - Get project details
- `GET /api/projects/{id}/requirements` - Get original requirements
- `GET /api/projects/{id}/logs` - Get generation logs

**Generation**
- `POST /api/generation/start` - Start new app generation
- `GET /api/generation/status/{id}` - Check generation status

### WebSocket

- `WS /ws/generation/{generation_id}` - Real-time progress updates

**Message format:**
```json
{
  "type": "progress",
  "step": "backend",
  "step_number": 3,
  "percentage": 50,
  "message": "Generating backend code..."
}
```

### Interactive API Docs

When the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Installation & Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- Git
- GitHub CLI (`gh`) configured with authentication

### Backend Setup

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize database**:
   ```bash
   cd orchestrator-ui/backend
   python init_db.py
   ```

3. **Configure environment variables**:
   Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

   Required variables:
   ```
   ADESSO_AI_HUB_KEY=your-api-key-here
   ADESSO_BASE_URL=https://adesso-ai-hub.3asabc.de/v1
   GITHUB_TOKEN=your-github-token
   ```

4. **Start the backend**:
   ```bash
   cd orchestrator-ui/backend
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/../.."
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   **Note:** Use `python -m uvicorn` instead of just `uvicorn` to ensure the correct Python environment is used.

   Backend runs at: **http://localhost:8000**

### Frontend Setup

1. **Install Node.js dependencies**:
   ```bash
   cd orchestrator-ui/frontend
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

   Frontend runs at: **http://localhost:5173**

3. **Build for production**:
   ```bash
   npm run build
   npm run preview
   ```

## Usage

### Generating an App

1. Open http://localhost:5173 in your browser
2. Fill in the generation form:
   - **MVP Description**: Describe your application
   - **Features**: List features (one per line)
   - **User Stories** (optional): Add user stories
   - **Tech Stack**: Select frontend, backend, database, deployment platform
3. Click "Generate App"
4. Watch real-time progress through 6 steps:
   - ✅ README Update
   - ✅ Design Phase
   - ✅ Backend Code
   - ✅ Frontend Code
   - ✅ CI/CD Pipeline
   - ✅ GitHub Publish
5. When complete, find your project in the history section with a GitHub link

### Editing a Project

1. In the Project History section, click "Edit" on any project
2. The form populates with the original requirements
3. Modify as needed and click "Generate App"
4. A new version is created (linked to the original requirements)

### Troubleshooting

**Backend won't start:**
- Verify `.env` is configured correctly
- Check Python dependencies: `pip install -r requirements.txt`
- Ensure database directory is writable: `ls -l database/`

**Frontend won't build:**
- Verify Node.js 18+ is installed: `node --version`
- Clear cache and reinstall: `rm -rf node_modules && npm install`

**WebSocket connection fails:**
- Check backend is running on port 8000
- Verify CORS settings in `main.py`
- Check browser console for error messages

**Generation fails:**
- Check backend logs for errors
- Verify `run_all_agents.py` works standalone
- Check API credentials in `.env`

## Development

### Adding a New API Endpoint

1. Create handler in `backend/api/`:
   ```python
   @router.get("/my-endpoint")
   def my_endpoint():
       return {"message": "Hello"}
   ```

2. Register router in `main.py`:
   ```python
   from orchestrator_ui.backend.api import my_api
   app.include_router(my_api.router)
   ```

### Adding a New React Component

1. Create component in `frontend/src/components/`:
   ```tsx
   export const MyComponent: React.FC = () => {
       return <div>My Component</div>;
   };
   ```

2. Import and use in `App.tsx`:
   ```tsx
   import MyComponent from './components/MyComponent';
   ```

### Database Migrations

The current setup uses SQLAlchemy's `create_all()` for simplicity. For production, consider:

1. **Alembic** for migrations:
   ```bash
   pip install alembic
   alembic init alembic
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

2. **Backup strategy**: Regular SQLite backups
   ```bash
   cp database/orchestrator.db database/orchestrator.db.backup
   ```

## Testing

### Backend Tests

```bash
cd orchestrator-ui/backend
pytest
```

### Frontend Tests

```bash
cd orchestrator-ui/frontend
npm test
```

### End-to-End Test

1. Start backend and frontend
2. Open http://localhost:5173
3. Submit generation form with test data:
   - Description: "Test weather app"
   - Features: "Show temperature"
   - Tech: React, none, none, github-pages
4. Verify progress indicator advances
5. Check project appears in history
6. Verify database has entry: `sqlite3 database/orchestrator.db "SELECT * FROM projects;"`

## Production Deployment

### Backend

Deploy to any Python hosting platform:

**Railway**:
```bash
railway up
```

**Render**:
Create `render.yaml`:
```yaml
services:
  - type: web
    name: orchestrator-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn orchestrator_ui.backend.main:app --host 0.0.0.0 --port $PORT
```

### Frontend

Deploy to Vercel:
```bash
cd orchestrator-ui/frontend
npm run build
vercel --prod
```

Or GitHub Pages:
```bash
npm run build
# Copy dist/ to gh-pages branch
```

## Security Considerations

- **Never commit `.env`**: Already in `.gitignore`
- **API keys**: Use environment variables only
- **Database**: SQLite is single-user; use PostgreSQL for multi-user
- **CORS**: Restrict origins in production
- **WebSocket**: Add authentication for production use

## Future Enhancements

- **Authentication**: JWT-based user authentication
- **Multi-user**: PostgreSQL + user accounts
- **Project versioning**: Track multiple generations per project
- **AI chat**: Conversational interface for requirements refinement
- **Code diff**: Compare iterations side-by-side
- **Deploy from UI**: Trigger Vercel/Railway deployments
- **Export**: Download project as ZIP

## License

Part of the Agentic Orchestra project.

## Support

For issues or questions:
- GitHub Issues: [agentic-orchestra/issues](https://github.com/your-org/agentic-orchestra/issues)
- Internal documentation: See main README.md
