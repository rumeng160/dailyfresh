from celery import Celery

app = Celery('taotest',backend='redis://127.0.0.1:6379/1',broker='redis://127.0.0.1:6379/2')
@app.task()
def cetest(a,b):
    print('任务函数正在执行')
    return a+b


