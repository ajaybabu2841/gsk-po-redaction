import functools
from utils.logging.error_handler import log_error_to_db

def capture_errors(stage, error_category="UnhandledStageError"):
    """
    Decorator that catches ANY exception inside the wrapped function
    and logs it to ErrorDump with stage/context.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except Exception as exc:
                log_error_to_db(
                    stage=stage,
                    error_category=error_category,
                    error_message=str(exc),
                    metadata={
                        "function": func.__name__,
                        "args": str(args),
                        "kwargs": str(kwargs),
                    }
                )
                raise  # rethrow so global handler also manages it
        return wrapper
    return decorator
