from zesje import celery, factory
from werkzeug.middleware.proxy_fix import ProxyFix

app = factory.create_app(celery=celery)

if app.config['PROXY_COUNT'] > 0:
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_proto=app.config['PROXY_COUNT'],
        x_for=app.config['PROXY_COUNT'],
    )
    print(app.config['PROXY_COUNT'])
