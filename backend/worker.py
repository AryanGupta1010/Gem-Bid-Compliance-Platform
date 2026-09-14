import os
from redis import Redis
from rq import Worker, Queue

listen = ['default']

from app.config import settings

conn = Redis.from_url(settings.REDIS_URL)

if __name__ == '__main__':
    queues = [Queue(name, connection=conn) for name in listen]
    
    # Use SimpleWorker on Windows because os.fork() is not available
    if os.name == 'nt':
        from rq import SimpleWorker
        worker = SimpleWorker(queues, connection=conn)
    else:
        worker = Worker(queues, connection=conn)
        
    print("Starting RQ worker...")
    worker.work()
