import os

from celery.result import AsyncResult
from flask_socketio import SocketIO, join_room, emit

from project import socketio

SOCKETIO_MESSAGE_QUEUE = os.environ.get(
    'SOCKETIO_MESSAGE_QUEUE',
    'redis://127.0.0.1:6379/0'
)

socketio_instance = SocketIO(message_queue=SOCKETIO_MESSAGE_QUEUE)


def get_task_info(task_id):
    task = AsyncResult(task_id)
    if task.state == 'FAILURE':
        error = str(task.result)
        response = {
            'state': task.state,
            'error': error,
        }
    else:
        response = {
            'state': task.state
        }

    return response


def update_celery_task_status(task_id):
    """
    This is function would be called in Celery Worker
    :param task_id:
    :return:
    """
    socketio_instance.emit('status', get_task_info(task_id), room=task_id, namespace='/task_status')


@socketio.on('join', namespace='/task_status')
def on_join(message):
    join_room(message['task_id'])

    emit('status', get_task_info(message['task_id']), room=message['task_id'])


