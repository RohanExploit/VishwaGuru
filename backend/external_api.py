"""
External API error handling utilities for VishwaGuru backend.
Provides retry logic, circuit breaker pattern, timeout management, and graceful degradation.
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any, Callable, Union
from enum import Enum
import httpx
from functools import wraps

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit breaker triggered
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """
    Circuit breaker implementation for external API calls.
    Prevents cascading failures when external services are down.
    """
    
    def __init__(
        self, 
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        return (
            self.last_failure_time and 
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Reset circuit breaker on successful call."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failure and potentially open circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker OPENED after {self.failure_count} failures")

class RetryConfig:
    """Configuration for retry logic."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

async def retry_with_backoff(
    func: Callable,
    config: RetryConfig,
    *args,
    **kwargs
) -> Any:
    """
    Execute function with exponential backoff retry logic.
    """
    last_exception = None
    
    for attempt in range(config.max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as e:
            last_exception = e
            
            if attempt == config.max_retries:
                logger.error(f"Max retries ({config.max_retries}) exceeded for {func.__name__}")
                break
            
            # Calculate delay with exponential backoff
            delay = min(
                config.base_delay * (config.exponential_base ** attempt),
                config.max_delay
            )
            
            # Add jitter to prevent thundering herd
            if config.jitter:
                import random
                delay *= (0.5 + random.random() * 0.5)
            
            logger.warning(
                f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                f"Retrying in {delay:.2f}s"
            )
            
            await asyncio.sleep(delay)
        
        except Exception as e:
            # Non-retryable exception
            logger.error(f"Non-retryable error in {func.__name__}: {str(e)}")
            raise e
    
    # If we get here, all retries failed
    raise last_exception

class ExternalAPIClient:
    """
    Enhanced HTTP client with retry logic, circuit breaker, and timeout management.
    """
    
    def __init__(
        self,
        base_url: str = "",
        timeout: float = 30.0,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        
        # HTTP client with timeout configuration
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
    
    async def post(
        self, 
        url: str, 
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        fallback_response: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        POST request with retry logic and circuit breaker protection.
        """
        full_url = f"{self.base_url}{url}" if self.base_url else url
        
        async def _make_request():
            try:
                response = await self.client.post(
                    full_url,
                    data=data,
                    files=files,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limiting
                    logger.warning(f"Rate limited by {full_url}. Status: {e.response.status_code}")
                    # Wait longer for rate limiting
                    await asyncio.sleep(5)
                raise e
            
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.warning(f"Network error for {full_url}: {str(e)}")
                raise e
        
        try:
            # Execute with circuit breaker and retry logic
            result = await retry_with_backoff(
                lambda: self.circuit_breaker.call(_make_request),
                self.retry_config
            )
            return result
        
        except Exception as e:
            logger.error(f"All attempts failed for {full_url}: {str(e)}")
            
            # Return fallback response if provided
            if fallback_response is not None:
                logger.info(f"Using fallback response for {full_url}")
                return fallback_response
            
            # Graceful degradation - return empty result
            return {"error": "Service temporarily unavailable", "detections": []}
    
    async def get(
        self, 
        url: str, 
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        fallback_response: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        GET request with retry logic and circuit breaker protection.
        """
        full_url = f"{self.base_url}{url}" if self.base_url else url
        
        async def _make_request():
            response = await self.client.get(
                full_url,
                params=params,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        
        try:
            result = await retry_with_backoff(
                lambda: self.circuit_breaker.call(_make_request),
                self.retry_config
            )
            return result
        
        except Exception as e:
            logger.error(f"GET request failed for {full_url}: {str(e)}")
            
            if fallback_response is not None:
                return fallback_response
            
            return {"error": "Service temporarily unavailable"}
    
    async def health_check(self, endpoint: str = "/health") -> bool:
        """
        Check if external service is healthy.
        """
        try:
            response = await self.client.get(
                f"{self.base_url}{endpoint}",
                timeout=5.0  # Short timeout for health checks
            )
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

# Global instances for different services
huggingface_client = ExternalAPIClient(
    base_url="https://api-inference.huggingface.co",
    timeout=30.0,
    retry_config=RetryConfig(max_retries=3, base_delay=2.0),
    circuit_breaker=CircuitBreaker(failure_threshold=5, recovery_timeout=120)
)

gemini_client = ExternalAPIClient(
    timeout=45.0,  # Longer timeout for AI services
    retry_config=RetryConfig(max_retries=2, base_delay=3.0),
    circuit_breaker=CircuitBreaker(failure_threshold=3, recovery_timeout=180)
)

async def monitor_external_services() -> Dict[str, bool]:
    """
    Monitor health of external services.
    """
    services = {
        "huggingface": await huggingface_client.health_check("/"),
        # Add other services as needed
    }
    
    # Log unhealthy services
    for service, is_healthy in services.items():
        if not is_healthy:
            logger.warning(f"External service {service} is unhealthy")
    
    return services