"""Rate limiting and retry utilities for API calls."""

from functools import wraps
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import openai
import time
from typing import Any, Callable, TypeVar, cast

T = TypeVar('T')

def with_rate_limit_retry(
    max_attempts: int = 3,
    min_wait: int = 4,
    max_wait: int = 60
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for handling rate limits with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries in seconds
        max_wait: Maximum wait time between retries in seconds
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(openai.RateLimitError),
            before_sleep=lambda retry_state: time.sleep(1)  # Small initial delay
        )
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except openai.RateLimitError as e:
                print(f"Rate limit hit, waiting before retry... (Attempt {retry_state.attempt_number})")
                raise
            except Exception as e:
                print(f"Unexpected error: {str(e)}")
                raise
        return cast(Callable[..., T], wrapper)
    return decorator
