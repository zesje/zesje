from flask import json


def mco_json():
    return {
        'x': 100,
        'y': 40,
        'problem_id': 1,
        'page': 1,
        'label': 'a',
        'name': 'test'
    }


def test_get_exams(test_client):
    mc_option_1 = {
        'x': 100,
        'y': 40,
        'problem_id': 3,
        'page': 1,
        'label': 'a',
        'name': 'test'
    }
    test_client.put('/api/mult-choice/', data=mc_option_1)

    mc_option_2 = {
        'x': 100,
        'y': 40,
        'problem_id': 3,
        'page': 1,
        'label': 'a',
        'name': 'test'
    }
    test_client.put('/api/mult-choice/', data=mc_option_2)

    response = test_client.get('/api/exams/3')
    data = json.loads(response.data)

    print(data)

    assert len(data['problems'][0]['mc_options']) == 2
