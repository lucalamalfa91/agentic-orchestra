# API Documentation

## Authentication Endpoints

### GET /api/auth/github/login
Returns GitHub OAuth authorization URL
- Response: `{"url": "https://github.com/login/oauth/authorize?..."}`

### GET /api/auth/github/callback?code=X
Exchanges code for JWT token
- Query params: `code` (from GitHub)
- Response: `{"token": "jwt_token", "user_id": 1}`

### GET /api/auth/github/status
Check GitHub connection
- Response: `{"connected": true, "username": "octocat"}`

## AI Provider Configuration

### POST /api/config/ai-provider
Save AI provider config
- Body: `{"base_url": "https://...", "api_key": "sk-..."}`
- Response: `{"status": "saved"}`

### GET /api/config/ai-provider
Get AI provider config (key not exposed)
- Response: `{"base_url": "https://..."}`

### POST /api/config/ai-provider/test
Test connection
- Body: `{"base_url": "https://...", "api_key": "sk-..."}`
- Response: `{"success": true}`

## Generation

### POST /api/generation/start
Start app generation
- Headers: `Authorization: Bearer jwt_token`
- Body: `{"mvp_description": "...", "tech_stack": {...}, "auto_decide": true}`
- Response: `{"id": "gen_123", "websocket_url": "ws://..."}`

### WS /ws/generation/{generation_id}
WebSocket for progress updates
- Messages: `{"step": 1, "status": "completed", "message": "..."}`

## Deploy Provider OAuth

### GET /api/auth/deploy/{provider}/login
Start OAuth for deploy provider (vercel, railway)
- Response: `{"url": "https://..."}`

### GET /api/auth/deploy/{provider}/callback?code=X
Exchange code for deploy token
- Response: `{"status": "ok"}`

## Error Responses

All errors return:
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

Common status codes:
- 400: Bad request
- 401: Unauthorized
- 404: Not found
- 500: Server error
