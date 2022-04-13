import random
import logging
import logging.config

import requests
from celery import shared_task
from celery.signals import task_postrun, setup_logging, after_setup_logger
from project.celery_utils import custom_celery_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task
def divide(x, y):
    # from celery.contrib import rdb
    # rdb.set_trace()

    import time
    time.sleep(5)
    return x / y


@shared_task
def sample_task(email):
    from project.users.views import api_call
    api_call(email)


@custom_celery_task(max_retries=3)
def task_process_notification():
    if not random.choice([0, 1]):
        # mimic random error
        raise Exception()

    requests.post('https://httpbin.org/delay/5')


@task_postrun.connect
def task_postrun_handler(task_id, **kwargs):
    from project.users.events import update_celery_task_status
    update_celery_task_status(task_id)


@shared_task()
def task_test_logger():
    logger.info('test')


# @setup_logging.connect()
# def on_setup_logging(**kwargs):
#     logging_dict = {
#         'version': 1,
#         'disable_existing_loggers': False,
#         'handlers': {
#             'file_log': {
#                 'class': 'logging.FileHandler',
#                 'filename': 'celery.log'
#             },
#             'default': {
#                 'class': 'logging.StreamHandler'
#             }
#         },
#         'loggers': {
#             'celery': {
#                 'handler': ['default', 'file_log'],
#                 'propagate': False,
#             }
#         },
#         'root': {
#             'handlers': ['default'],
#             'level': 'INFO'
#         }
#     }
#
#     # display task_id and task_name in task log
#     from celery.app.log import TaskFormatter
#     celery_logger = logging.getLogger('celery')
#     for handler in celery_logger.handlers:
#         handler.setFormatter(
#             TaskFormatter(
#                 '[%(asctime)s: %(levelname)s/%(processName)s/%(thread)d] [%(task_name)s(%(task_id)s)] %(message)s'
#             )
#         )


@shared_task(bind=True)
def task_add_subscribe(self, user_pk):
    try:
        from project.users.models import User
        user = User.query.get(user_pk)
        requests.post(
            'https://httpbin.org/delay/5',
            data={'email': user.email}
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@after_setup_logger.connect()
def on_after_setup_logger(logger, **kwargs):
    # print(f'logger {logger}, type {type(logger)}')
    # print(f'logger.handlers {logger.handlers[0]}, type {type(logger.handlers[0])}')
    # logger <RootLogger root (INFO)>, type <class 'logging.RootLogger'>
    # logger.handlers <StreamHandler <stderr> (NOTSET)>, type <class 'logging.StreamHandler'>
    formatter = logger.handlers[0].formatter
    file_handler = logging.FileHandler('celery.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


@shared_task()
def task_send_welcome_email():
    print('.......welcome........')