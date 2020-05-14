from zesje.database import db


def test_full_empty(test_client):
    response = test_client.get('/api/export/full')
    assert response.status_code == 200

    sql_data = response.data.decode('utf-8')
    for table in db.metadata.tables:
        assert table in sql_data
