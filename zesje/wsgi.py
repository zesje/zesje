from zesje import celery, factory

app = factory.create_app(celery=celery)
