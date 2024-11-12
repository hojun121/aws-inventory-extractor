import time
import random

def exponential_backoff(func, max_attempts=5, *args, **kwargs):
    attempt = 0
    while attempt < max_attempts:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Only retry for throttling errors
            if getattr(e, 'response', {}).get('Error', {}).get('Code') in ['Throttling', 'ThrottlingException', 'RequestLimitExceeded', 'TooManyRequestsException']:
                attempt += 1
                if attempt == max_attempts:
                    raise e
                sleep_time = min((2 ** attempt) + random.uniform(0, 1), 30)  # Limit sleep to 30 seconds
                print(f"Attempt {attempt} failed: {e}. Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
            else:
                raise e
