from zesje import factory

# Provides a flask app instance used by alembic for running migrations
app = factory.create_migrations_app()
