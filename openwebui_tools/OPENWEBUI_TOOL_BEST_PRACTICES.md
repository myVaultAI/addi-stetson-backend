# OpenWebUI Custom Tool Development - Best Practices

**Based on:** Real debugging session October 22, 2025  
**Purpose:** Avoid common Pydantic schema generation errors in OpenWebUI tools

---

## 🚨 Critical: Pydantic v2 Compatibility

### Issue: Schema Generation Errors

**Error Message:**
```
ERROR: Unable to generate pydantic-core schema for <class 'X'>. 
Set `arbitrary_types_allowed=True` in the model_config...
```

### Root Causes Discovered:

#### 1. **Pydantic v1 vs v2 Import Conflicts**

**❌ WRONG - Causes schema errors:**
```python
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
```

**✅ CORRECT - Pydantic v2 compatible:**
```python
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
```

**Why:** The `validator` decorator is a Pydantic v1 feature. Even if you don't use it, importing it causes incompatibility issues with Pydantic v2's schema generation. OpenWebUI introspects all imports.

**Migration Note:** In Pydantic v2, use `field_validator` or `model_validator` instead of `validator`.

---

#### 2. **Type Hints on Exception Parameters**

**❌ WRONG - Can cause introspection errors:**
```python
async def _handle_http_error(
    self, 
    error: httpx.HTTPStatusError,  # ❌ Complex type hint
    __event_emitter__=None
) -> str:
    ...

async def _handle_generic_error(
    self, 
    error: Exception,  # ❌ Base Exception type
    __event_emitter__=None
) -> str:
    ...
```

**✅ CORRECT - No type hints on error objects:**
```python
async def _handle_http_error(
    self, 
    error,  # ✅ No type hint
    __event_emitter__=None
) -> str:
    status_code = error.response.status_code  # Still works!
    ...

async def _handle_generic_error(
    self, 
    error,  # ✅ No type hint
    __event_emitter__=None
) -> str:
    ...
```

**Why:** OpenWebUI introspects ALL methods (including private/helper methods). Type hints using complex exception types can trigger schema generation errors. The code still works without the type hints - Python is dynamically typed!

---

#### 3. **Complex Object Storage in Tool Class**

**❌ WRONG - Not serializable:**
```python
class Tools:
    def __init__(self):
        self._client: httpx.AsyncClient = httpx.AsyncClient()  # ❌
        self._lock = asyncio.Lock()  # ❌
        self._cache = TTLCache(maxsize=100, ttl=300)  # ❌
```

**✅ CORRECT - Simple, serializable objects:**
```python
class Tools:
    def __init__(self):
        self._cache = {}  # ✅ Simple dict
        # Create httpx client per-request instead
```

**Why:** Pydantic needs to serialize the Tools class. Complex objects like HTTP clients, locks, and advanced cache objects can't be serialized.

**Solution:** Create complex objects as needed (e.g., `async with httpx.AsyncClient()`) rather than storing them.

---

## ✅ Proven Working Pattern

Based on **Stetson Knowledge Tool** (working perfectly) and **Call Analytics Tool v2.0.2** (fixed):

```python
"""
title: Your Tool Name
description: Tool description
author: DME-CPH Team
version: 1.0.0
requirements: httpx>=0.26.0, pydantic>=2.5.0, pydantic-settings>=2.0.0
"""

import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field  # ✅ NO validator import
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Tools:
    class Valves(BaseSettings):
        """Tool configuration"""
        BACKEND_URL: str = Field(
            default="http://localhost:44000",
            description="Backend API URL"
        )
        TIMEOUT: int = Field(
            default=30,
            description="Request timeout in seconds"
        )
        
        model_config = SettingsConfigDict(
            env_prefix='YOUR_TOOL_',
            case_sensitive=True
        )
    
    def __init__(self):
        self.valves = self.Valves()
        self.citation = True
        
        # ✅ Only simple objects
        self._cache = {}
    
    async def your_main_function(
        self,
        param: str,
        __user__: dict = {},
        __event_emitter__=None
    ) -> str:
        """Main tool function"""
        try:
            # ✅ Create HTTP client per-request
            async with httpx.AsyncClient(timeout=self.valves.TIMEOUT) as client:
                response = await client.get(f"{self.valves.BACKEND_URL}/api/endpoint")
                response.raise_for_status()
                data = response.json()
                return self._format_response(data)
                
        except httpx.HTTPStatusError as e:
            return await self._handle_http_error(e, __event_emitter__)
        except Exception as e:
            return await self._handle_generic_error(e, __event_emitter__)
    
    def _format_response(self, data: dict) -> str:
        """Format response - regular method, no complex types"""
        return f"Result: {data}"
    
    async def _handle_http_error(
        self, 
        error,  # ✅ NO type hint
        __event_emitter__=None
    ) -> str:
        """Handle HTTP errors"""
        status_code = error.response.status_code
        return f"❌ HTTP Error {status_code}"
    
    async def _handle_generic_error(
        self, 
        error,  # ✅ NO type hint
        __event_emitter__=None
    ) -> str:
        """Handle generic errors"""
        return f"❌ Error: {str(error)}"
```

---

## 📋 Pre-Import Checklist

Before importing a tool to OpenWebUI, verify:

### Imports:
- [ ] No `validator` import from pydantic
- [ ] Using `pydantic-settings` for BaseSettings (not pydantic.settings)
- [ ] All imports are Pydantic v2 compatible

### Class Structure:
- [ ] `Tools` class with `Valves` inner class
- [ ] `__init__` only stores simple objects (dict, list, str, int, bool)
- [ ] No stored AsyncClient, Lock, or complex cache objects

### Type Hints:
- [ ] Error handler parameters have NO type hints
- [ ] Helper methods don't use Exception, HTTPStatusError type hints
- [ ] Main function parameters can have basic type hints (str, int, bool, dict)

### Requirements:
- [ ] Requirements line specifies correct package versions
- [ ] All packages are actually installed in environment
- [ ] Pydantic v2 packages: `pydantic>=2.5.0`, `pydantic-settings>=2.0.0`

---

## 🔧 Debugging Tips

### If you get schema generation error:

1. **Check imports first:**
   - Remove any Pydantic v1 features (`validator`, `constr`, etc.)
   - Make sure `pydantic-settings` is used, not `pydantic.settings`

2. **Check stored objects:**
   - Remove any `self._client`, `self._lock`, `self._cache` if they're complex
   - Replace with simple dicts or create objects per-request

3. **Check type hints:**
   - Remove type hints from error handlers
   - Remove type hints from helper methods with complex types

4. **Test incrementally:**
   - Start with minimal tool (just Valves and one function)
   - Add features one at a time
   - Re-import after each addition to find what breaks

### Quick Test:

Create a minimal test tool:
```python
class Tools:
    class Valves(BaseSettings):
        TEST: str = Field(default="test")
        model_config = SettingsConfigDict(case_sensitive=True)
    
    def __init__(self):
        self.valves = self.Valves()
    
    async def test_function(self, query: str) -> str:
        return f"Test: {query}"
```

If this imports successfully, the problem is in your added code, not the base structure.

---

## 📚 Reference Documentation

### Pydantic v2 Migration Guide:
- https://docs.pydantic.dev/latest/migration/

### Key Changes from v1 to v2:
- `validator` → `field_validator` or `model_validator`
- `Config` class → `model_config` dict
- `pydantic.settings` → `pydantic-settings` package
- Settings use `SettingsConfigDict` not `Config`

### OpenWebUI Tool Documentation:
- OpenWebUI introspects the entire Tools class
- All methods are checked, even private ones
- Type hints matter because of introspection
- Simple is better - avoid complex object storage

---

## 🎓 Lessons Learned - October 22, 2025

**Context:** Call Analytics Tool v2.0.0 → v2.0.2 debugging session

**Problem:** Pydantic schema generation errors preventing tool import

**Root Causes Found:**
1. `validator` import (Pydantic v1 feature) in v2 codebase
2. Type hints on exception parameters triggering introspection issues
3. Complex objects stored in class (AsyncClient, Lock, TTLCache)

**Solutions Applied:**
1. Removed `validator` from imports → Fixed immediately
2. Removed type hints from error handlers → Fixed edge cases
3. Simplified to dict-based caching → Compatible with Pydantic serialization

**Result:** Tool v2.0.2 imports and runs perfectly ✅

**Key Insight:** OpenWebUI tools need to be SIMPLE. Don't try to be too clever with advanced patterns. Create HTTP clients per-request, use simple dicts for caching, avoid complex type hints. The "naive" approach works best.

---

## ✅ Success Stories

### Working Tools (Proven Patterns):

1. **Stetson Knowledge Tool v1.0.0**
   - ✅ Creates AsyncClient per-request
   - ✅ No complex object storage
   - ✅ No Pydantic v1 imports
   - **Status:** Working perfectly since first import

2. **Call Analytics Tool v2.0.2**
   - ✅ Simple dict caching
   - ✅ No type hints on error handlers
   - ✅ Pydantic v2 compatible
   - **Status:** Fixed and working

### Failed Attempts (Learn from these):

1. **Call Analytics Tool v2.0.0**
   - ❌ Persistent AsyncClient with connection pooling
   - ❌ TTLCache from cachetools
   - ❌ asyncio.Lock storage
   - **Status:** Pydantic schema error

2. **Call Analytics Tool v2.0.1**
   - ❌ Added `arbitrary_types_allowed=True` (didn't work)
   - ❌ Still had `validator` import
   - ❌ Still had Exception type hints
   - **Status:** Still errored

3. **Call Analytics Tool v2.0.2**
   - ✅ Removed validator import
   - ✅ Removed Exception type hints
   - ✅ Simple dict caching
   - **Status:** SUCCESS! ✅

---

**Remember:** Keep it simple. OpenWebUI tools should be straightforward. Save the fancy patterns for backend services where they belong.

**Version:** 1.0  
**Last Updated:** October 22, 2025  
**Tested With:** OpenWebUI (non-Docker), Pydantic v2.12.3, Python 3.11

