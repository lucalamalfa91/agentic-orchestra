# Authentication Flow Improvement - 2026-04-11

## 🎯 Obiettivo

Implementare gestione robusta di token JWT scaduti/invalidi con UX migliorata per errori di autenticazione gh CLI.

---

## ✅ Modifiche Implementate

### 1. **AuthContext.tsx** - Aggiunto `login()` e `logout()`

**Prima**: Missing `login()` function → runtime error in AuthScreen

**Dopo**:
```typescript
login: (token: string) => void        // Salva token e effettua login
logout: () => void                     // Rimuove token e user
```

### 2. **api/client.ts** - Interceptor 401 automatico

**Prima**: 401 → solo console.error, user rimane "loggato" con token invalido

**Dopo**:
```typescript
if (error.response?.status === 401) {
  localStorage.removeItem('jwt_token');              // Invalida token
  sessionStorage.setItem('auth_redirect', pathname); // Salva destinazione
  window.location.href = '/auth?session_expired=true'; // Redirect con flag
}
```

**Benefici**:
- ✅ Token scaduto/invalido → logout automatico
- ✅ Redirect a /auth con messaggio "Sessione scaduta"
- ✅ Dopo re-login, torna alla pagina originale (sessionStorage)

### 3. **AuthScreen.tsx** - UX migliorata per errori gh CLI

**Prima**: Errore generico "Failed to authenticate"

**Dopo**:
- ⚠️ Warning giallo: "Your session has expired. Please log in again."
- 🔴 Error dettagliato con istruzioni:
  - "GitHub CLI authentication expired. Please run: gh auth refresh"
  - "GitHub CLI not configured. Please run: gh auth login"
- 📋 Code snippet visibile: `gh auth refresh` in box con sfondo scuro

**Flow**:
```typescript
1. Rileva query param ?session_expired=true → mostra warning
2. Catch error da loginWithGhCLI()
3. Parse error message:
   - "Bad credentials" / "401" → "gh auth refresh"
   - "not authenticated" → "gh auth login"
4. Mostra istruzioni chiare con comando da eseguire
```

### 4. **backend/api/auth.py** - Messaggi di errore chiari

**Prima**:
```python
raise HTTPException(status_code=401, detail="gh CLI not authenticated. Run: gh auth login")
```

**Dopo**:
```python
error_msg = result.stderr.strip() if result.stderr else "gh CLI not authenticated"
raise HTTPException(
    status_code=401,
    detail=f"gh CLI authentication failed: {error_msg}. Please run 'gh auth login' or 'gh auth refresh'"
)
```

**Benefici**:
- ✅ Include stderr originale (es: "Bad credentials")
- ✅ Suggerisce entrambi i comandi (login/refresh)

### 5. **start-backend.sh** - GitHub CLI nel PATH

**Aggiunto**:
```bash
GH_CLI_PATH="/c/Program Files/GitHub CLI"
if [ -d "$GH_CLI_PATH" ] && [[ ":$PATH:" != *":$GH_CLI_PATH:"* ]]; then
    export PATH="$GH_CLI_PATH:$PATH"
fi
```

**Benefici**:
- ✅ Backend può eseguire `gh` anche se non nel PATH di sistema
- ✅ Fix per Windows dove gh potrebbe non essere nel PATH di Python

---

## 🔄 Nuovo Flusso Autenticazione

### Scenario 1: Utente non autenticato (primo accesso)

```
1. User apre app → App.tsx: if (!token) return <Navigate to="/auth" />
2. AuthScreen mostra → "Connect with GitHub"
3. Click → loginWithGhCLI()
4. gh CLI OK → riceve JWT → localStorage + redirect a /
5. gh CLI KO → mostra errore + istruzioni
```

### Scenario 2: Token JWT scaduto (utente già loggato)

```
1. User fa azione → API call con token vecchio
2. Backend → 401 Unauthorized
3. Interceptor → rileva 401:
   - Rimuove jwt_token da localStorage
   - Salva URL corrente in sessionStorage
   - Redirect a /auth?session_expired=true
4. AuthScreen mostra:
   - ⚠️ "Your session has expired. Please log in again."
   - Button "Connect with GitHub"
5. User re-login → torna alla pagina originale
```

### Scenario 3: gh CLI token scaduto/invalido

```
1. User click "Connect with GitHub"
2. Backend chiama: gh api user -q ".login,.id"
3. gh restituisce: "Bad credentials (HTTP 401)"
4. Backend → HTTPException(401, "gh CLI authentication failed: Bad credentials...")
5. Frontend catch error → parse message:
   - Rileva "Bad credentials" → mostra "gh auth refresh"
   - Mostra box con comando e istruzioni
6. User esegue: gh auth refresh (in terminale)
7. User click di nuovo "Connect with GitHub" → login OK ✅
```

---

## 📁 File Modificati

| File | Modifiche | Righe |
|------|-----------|-------|
| `frontend/src/context/AuthContext.tsx` | +login(), +logout() | +8 |
| `frontend/src/api/client.ts` | +401 interceptor | +13 |
| `frontend/src/screens/AuthScreen.tsx` | +session expired, +gh error UX | +35 |
| `backend/api/auth.py` | +better error messages | +3 |
| `start-backend.sh` | +GitHub CLI PATH | +5 |
| `.env` | Commented DATABASE_URL | +2 |

**Totale**: 6 file, ~66 righe modificate

---

## 🧪 Testing

### Test 1: Token scaduto
```bash
# Simula token scaduto nel localStorage
localStorage.setItem('jwt_token', 'invalid.token.here')

# Fai una richiesta API → dovrebbe redirect a /auth con warning
```

### Test 2: gh CLI non autenticato
```bash
# Invalida gh CLI
gh auth logout

# Vai a /auth e click "Connect with GitHub"
# Dovrebbe mostrare: "Please run: gh auth login"
```

### Test 3: gh CLI token scaduto
```bash
# Attendi scadenza token gh (o invalida manualmente)
# Click "Connect with GitHub"
# Dovrebbe mostrare: "Please run: gh auth refresh"
```

---

## 🎯 Risultati

### Prima
- ❌ Token scaduto → user vede errori 401 su ogni azione, nessun logout
- ❌ gh CLI error → messaggio generico "Failed to authenticate"
- ❌ Nessuna istruzione su come risolvere
- ❌ AuthContext.login() missing → runtime error

### Dopo
- ✅ Token scaduto → logout automatico + redirect con messaggio chiaro
- ✅ gh CLI error → istruzioni specifiche con comando da eseguire
- ✅ UX professionale con warning/error visivamente distinti
- ✅ AuthContext completo con login/logout

---

## 📝 Note Tecniche

1. **Perché `window.location.href` invece di `navigate()`?**
   - L'interceptor axios è fuori dal React context
   - `window.location.href` forza un hard reload, garantendo reset completo dello stato

2. **sessionStorage vs localStorage per redirect?**
   - sessionStorage → cancellato quando tab chiuso (sicurezza)
   - localStorage → persiste tra sessioni (non ideale per redirect temporanei)

3. **Perché non JWT decode per verificare scadenza?**
   - Backend già controlla scadenza e restituisce 401
   - Evita duplicazione logica frontend/backend
   - Più sicuro (backend è source of truth)

---

## 🚀 Next Steps (Future)

- [ ] Refresh token automatico prima della scadenza
- [ ] Toast notification invece di reload per 401 (UX più smooth)
- [ ] OAuth GitHub come alternativa a gh CLI
- [ ] Session timeout warning (es: "Sessione scade tra 5 minuti")
