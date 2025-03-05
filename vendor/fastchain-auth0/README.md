# FastChain Auth0 Integration

A framework-agnostic Auth0 authentication package with advanced features and optional framework integrations.

## Features

- Core Auth0 functionality:
  - Async JWT token validation and verification
  - Enhanced rate limiting with automatic cleanup
  - Token refresh handling with rotation support
  - User information extraction from tokens
  - Permission-based authorization
  - Configurable authentication settings
  - Framework-agnostic design
- Advanced async features:
  - Full async context manager support
  - Automatic session management
  - Efficient JWKS caching
  - Connection pooling and timeouts
  - Background cleanup tasks
- Framework integrations (optional, available separately)

## Installation

### Basic Installation
For core Auth0 functionality only:
```bash
pip install -e vendor/fastchain-auth0
```

## Usage

### Async Token Verification with Advanced Rate Limiting

```python
from fastchain_auth0 import Auth0Config, Auth0Manager, JWTError, RateLimitExceeded
import asyncio

async def verify_token_example():
    # Configure Auth0
    auth0_config = Auth0Config(
        domain="your-tenant.auth0.com",
        api_audience="your-api-identifier"
    )

    # Create Auth0 manager with rate limiting and automatic cleanup
    async with Auth0Manager(
        auth0_config,
        rate_limit_max=100,
        rate_limit_window=60
    ) as auth0_manager:
        try:
            # Verify token asynchronously
            user = await auth0_manager.get_user_from_token(token)
            print(f"Authenticated user: {user.sub}")
            print(f"User permissions: {user.permissions}")
        except RateLimitExceeded as e:
            print(f"Rate limit exceeded: {e}")
            # Get remaining requests and reset time
            remaining, reset_in = await auth0_manager.get_remaining_requests(token)
            print(f"Remaining requests: {remaining}, resets in {reset_in} seconds")
        except JWTError as e:
            print(f"Authentication failed: {e}")

# Run the async example
asyncio.run(verify_token_example())
```

### Token Refresh Handling with Rotation

```python
from fastchain_auth0 import TokenRefreshManager, JWTError
import asyncio

async def refresh_token_example():
    # Initialize token refresh manager with async context support
    async with TokenRefreshManager(
        domain="your-tenant.auth0.com",
        client_id="your-client-id",
        client_secret="your-client-secret",
        default_audience="your-api-identifier"
    ) as refresh_manager:
        try:
            # Refresh token with optional rotation
            new_tokens = await refresh_manager.refresh_token(
                refresh_token="your-refresh-token",
                scope="openid profile email",  # Optional
                rotate=True  # Enable refresh token rotation
            )

            print(f"New access token: {new_tokens['access_token']}")
            print(f"Expires in: {new_tokens['expires_in']} seconds")

            if 'refresh_token' in new_tokens:
                print("Refresh token was rotated")

        except JWTError as e:
            print(f"Token refresh failed: {e}")

# Run the async example
asyncio.run(refresh_token_example())
```

## Configuration

### Auth0Config Parameters
- `domain`: Your Auth0 domain (e.g., 'your-tenant.auth0.com')
- `api_audience`: API audience identifier
- `algorithms`: Token signing algorithms (default: ["RS256"])
- `issuer`: Token issuer (optional, defaults to https://your-domain/)

### Rate Limiting Configuration
The `Auth0Manager` accepts rate limiting parameters with enhanced features:
- `rate_limit_max`: Maximum number of requests in the window (default: 100)
- `rate_limit_window`: Time window in seconds (default: 60)
- `cleanup_interval`: Interval for rate limit data cleanup (default: 60)

### TokenRefreshManager Parameters
- `domain`: Auth0 domain
- `client_id`: Auth0 application client ID
- `client_secret`: Auth0 application client secret
- `default_audience`: Default API audience (optional)
- `timeout`: Request timeout in seconds (default: 10)

## Advanced Features

### Automatic Session Management
The package now includes intelligent session management:
```python
async with Auth0Manager(auth0_config) as manager:
    # Session is automatically created and managed
    user = await manager.get_user_from_token(token)
    # Session is automatically cleaned up on exit
```

### Enhanced Error Handling
The package provides comprehensive error handling with detailed information:

```python
try:
    user = await auth0_manager.get_user_from_token(token)
except RateLimitExceeded as e:
    remaining, reset_in = await auth0_manager.get_remaining_requests(token)
    print(f"Rate limit exceeded. Retry after {reset_in} seconds")
except JWTError as e:
    print(f"Token validation failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Connection Pooling and Timeouts
Built-in support for connection pooling and configurable timeouts:
```python
auth0_manager = Auth0Manager(
    auth0_config,
    timeout=10,  # Request timeout in seconds
    pool_connections=10,  # Maximum connections in pool
    pool_maxsize=10  # Maximum size of connection pool
)
```

## Development

### Running Tests
```bash
# Install test dependencies
pip install -e vendor/fastchain-auth0[test]

# Run tests with coverage
pytest tests/
```

## License

MIT