import functools

from celery import current_app as current_celery_app
from celery.utils.time import get_exponential_backoff_interval
from celery import Task, shared_task


def make_celery(app):
    celery = current_celery_app
    celery.config_from_object(app.config, namespace='CELERY')

    return celery


class custom_celery_task:
    EXCEPTION_BLOCK_LIST = (
        IndexError,
        KeyError,
        TypeError,
        UnicodeDecodeError,
        ValueError,
    )

    def __init__(self, *args, **kwargs):
        self.task_args = args
        self.task_kwargs = kwargs

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper_func(*args, **kwargs):
            try:
                with task_func.app.flask_app.app_context():
                    return func(*args, **kwargs)
            except self.EXCEPTION_BLOCK_LIST:
                # do not retry for those exceptions
                raise
            except Exception as e:
                # here we add Exponential Backoff just like Celery
                countdown = self._get_retry_countdown(task_func)
                raise task_func.retry(exc=e, countdown=countdown)

        task_func = shared_task(*self.task_args, **self.task_kwargs)(wrapper_func)
        return task_func

    def _get_retry_countdown(self, task_func):
        retry_backoff = int(
            self.task_kwargs.get('retry_backoff', True)
        )
        retry_backoff_max = int(
            self.task_kwargs.get('retry_backoff_max', 600)
        )
        retry_jitter = self.task_kwargs.get(
            'retry_jitter', True
        )

        countdown = get_exponential_backoff_interval(
            factor=retry_backoff,
            retries=task_func.request.retries,
            maximum=retry_backoff_max,
            full_jitter=retry_jitter
        )

        return countdown
