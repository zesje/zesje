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


def test_get_no_exam(test_client):
    result = test_client.get('/api/mult-choice/1')
    data = json.loads(result.data)

    assert data['message'] == "Multiple choice question with id 1 does not exist."


def test_add_exam(test_client):
    req = mco_json()
    response = test_client.put('/api/mult-choice/', data=req)

    data = json.loads(response.data)

    assert data['message'] == 'New multiple choice question with id 4 inserted. ' \
        + 'New feedback option with id 1 inserted.'

    assert data['mult_choice_id'] == 4
    assert data['status'] == 200


def test_add_get(test_client):
    req = mco_json()

    response = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)

    id = data['mult_choice_id']

    result = test_client.get(f'/api/mult-choice/{id}')
    data = json.loads(result.data)

    exp_resp = {
        'id': 5,
        'name': 'test',
        'x': 100,
        'y': 40,
        'type': 'mcq_widget',
        'feedback_id': 2,
        'label': 'a',
    }

    assert exp_resp == data


def test_update_put(test_client):
    req = mco_json()

    response = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)
    id = data['mult_choice_id']

    req2 = {
        'x': 120,
        'y': 50,
        'problem_id': 4,
        'page': 1,
        'label': 'b',
        'name': 'test'
    }

    result = test_client.put(f'/api/mult-choice/{id}', data=req2)
    data = json.loads(result.data)

    assert data['message'] == f'Multiple choice question with id {id} updated'


def test_delete(test_client):
    req = mco_json()

    response = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)
    id = data['mult_choice_id']

    response = test_client.delete(f'/api/mult-choice/{id}')
    data = json.loads(response.data)

    assert data['status'] == 200


def test_delete_not_present(test_client):
    id = 100

    response = test_client.delete(f'/api/mult-choice/{id}')
    data = json.loads(response.data)

    assert data['message'] == f'Multiple choice question with id {id} does not exist.'


def test_delete_finalized_exam(test_client):
    mc_option_json = {
        'x': 100,
        'y': 40,
        'problem_id': 2,
        'page': 1,
        'label': 'a',
        'name': 'test'
    }

    response = test_client.put('/api/mult-choice/', data=mc_option_json)
    data = json.loads(response.data)
    mc_id = data['mult_choice_id']

    response = test_client.delete(f'/api/mult-choice/{mc_id}')
    data = json.loads(response.data)

    assert data['status'] == 401
