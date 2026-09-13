import os
from redis import Redis
from rq import Worker, Queue

listen = ['default']

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
conn = Redis.from_url(redis_url)

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
