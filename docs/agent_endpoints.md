# Agent Endpoint Implementation

This document outlines the design and implementation guidelines for building agent-specific API endpoints using FastAPI. It explains how to organize endpoints by agent, handle authentication and permissions, and manage dependencies on a per-agent basis. This approach promotes a clear separation of concerns, improves maintainability, and allows for flexible scaling as your multi-agent system evolves.

---

## 1. Grouping Endpoints by Agent

In a multi-agent system, different agents typically encapsulate distinct business logic or serve separate service domains (e.g., customer support, intent processing, data retrieval). Organizing endpoints by agent offers several benefits:

- **Distinct Business Domains:** Each agent has its own dedicated endpoints that encapsulate its domain-specific functionality.
- **Separation of Concerns:** Grouping endpoints by agent allows you to manage dependencies, authentication rules, and rate limiting separately for each agent.
- **Scalability:** As the project grows, adding or modifying an agent’s API is easier because changes remain isolated within that agent’s module.

### Example Directory Structure

An example structure for grouping endpoints by agent may look like this:

```
src/
├── api/
│   ├── v1/
│   │   ├── agents/
│   │   │   ├── intent/
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── query.py             # Endpoints specific to intent processing
│   │   │   │   │   └── classification.py    # Endpoints for classification operations
│   │   │   │   ├── dependencies.py          # Agent-specific dependencies (e.g., DB sessions, third-party APIs)
│   │   │   │   └── schemas.py               # Data models for intent-related requests and responses
│   │   │   ├── support/
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── tickets.py             # Endpoints for support ticket management
│   │   │   │   ├── dependencies.py          # Support agent-specific dependencies and permissions
│   │   │   │   └── schemas.py               # Data models for support-related endpoints
│   │   ├── dependencies.py        # Global dependencies for v1 if needed
│   │   ├── routers.py             # Aggregates agent routers into a unified v1 router
│   │   ├── schemas.py             # Global schemas for v1 if applicable
│   ├── main_router.py             # Registers all API versions with the FastAPI app
```

This structure keeps endpoints organized by agent, allowing each agent to have its own dependency injection setup and rate-limiting or authentication rules.

---

## 2. Handling Authentication

FastAPI offers robust support for authentication through OAuth2 and JWT (JSON Web Tokens). Using authentication dependencies not only secures your endpoints but also allows you to enforce agent-specific authorization rules.

### 2.1 Define an Authentication Dependency

Create a dependency that validates JWT tokens and extracts user information. For example:

```python
# src/api/v1/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

# OAuth2 scheme with a token URL (endpoint to obtain a token)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT configuration
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        # Optionally, fetch user details from your database using user_id
        return {"user_id": user_id, "roles": payload.get("roles", [])}
    except JWTError:
        raise credentials_exception
```

### 2.2 Apply the Dependency to Agent Endpoints

For endpoints that require authentication, add the dependency. For example, in an intent agent endpoint:

```python
# src/api/v1/agents/intent/endpoints/query.py

from fastapi import APIRouter, Depends
from src.api.v1.dependencies import get_current_user
from src.api.v1.agents.intent.schemas import QueryRequest, QueryResponse

router = APIRouter()

@router.post("/query", response_model=QueryResponse, tags=["Intent"])
async def process_intent_query(
    request: QueryRequest, 
    current_user: dict = Depends(get_current_user)
):
    # Process the intent query using the Intent Agent's logic
    # The current_user dict contains authenticated user details
    result = {"intent": "classified_intent", "confidence": 0.92}
    return QueryResponse(**result)
```

### 2.3 Agent-Specific Authentication Rules

Sometimes, an agent may require additional verification. For instance, a support agent might need to check if a user has a support role:

```python
# src/api/v1/agents/support/dependencies.py

from fastapi import Depends, HTTPException
from src.api.v1.dependencies import get_current_user

def get_support_user(current_user: dict = Depends(get_current_user)):
    if "support" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not authorized for support agent access")
    return current_user
```

Then, apply this dependency to support endpoints:

```python
# src/api/v1/agents/support/endpoints/tickets.py

from fastapi import APIRouter, Depends
from src.api.v1.agents.support.dependencies import get_support_user

router = APIRouter()

@router.get("/tickets", tags=["Support"])
async def list_support_tickets(user: dict = Depends(get_support_user)):
    # Return support tickets for the authenticated support user
    return {"tickets": []}
```

---

## 3. Integrating Endpoints with Agent Routing

### Aggregating Routers

The main router aggregates agent-specific routers into one unified API version. This is usually done in `routers.py`:

```python
# src/api/v1/routers.py

from fastapi import APIRouter
from src.api.v1.agents.intent.endpoints import query as intent_query
from src.api.v1.agents.support.endpoints import tickets as support_tickets

router = APIRouter()

# Include agent-specific routers
router.include_router(intent_query.router, prefix="/intent", tags=["Intent"])
router.include_router(support_tickets.router, prefix="/support", tags=["Support"])
```

And register the global router in `main_router.py`:

```python
# src/api/main_router.py

from fastapi import FastAPI
from src.api.v1.routers import router as api_v1_router

app = FastAPI(title="Multi-Agent System API", version="1.0")

app.include_router(api_v1_router, prefix="/api/v1")
```

---

## 4. Summary

- **Endpoint Structuring:**  
  Organize endpoints by agent to encapsulate distinct business domains and to facilitate independent development, dependency management, and scalability.

- **Authentication:**  
  Utilize FastAPI’s dependency injection to enforce OAuth2 and JWT-based authentication. Define agent-specific dependencies if necessary, ensuring that endpoints are secured and user roles are appropriately validated.

- **Modular Router Aggregation:**  
  Use modular routers for each agent and aggregate them in a central router for a cohesive API design. This enhances maintainability and makes it easier to manage large projects.

---
