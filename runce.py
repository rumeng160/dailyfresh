from test import cetest
from celery.result import ResultBase

r = cetest.delay(1,2)
print(r)
print(r.failed())
print([v for v in r.collect() if not isinstance(v, (ResultBase, tuple))])


