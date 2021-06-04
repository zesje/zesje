import pytest

from flask import json

from zesje.database import db, Exam, Problem, ProblemWidget, FeedbackOption


@pytest.fixture
def add_test_data(app):
    exam1 = Exam(id=1, name='exam 1', finalized=False)
    db.session.add(exam1)

    problem1 = Problem(id=1, name='Problem 1', exam_id=1)

    db.session.add(problem1)

    problem_widget_1 = ProblemWidget(id=1, name='problem widget', problem_id=1, page=2,
                                     width=100, height=150, x=40, y=200, type='problem_widget')
    db.session.add(problem_widget_1)

    root = FeedbackOption(id=12, problem_id=1, text='root')
    db.session.add(root)
    db.session.commit()
    fo1 = FeedbackOption(id=5, problem_id=1, text='fully incorrect', score=2, parent_id=12)
    db.session.add(fo1)
    db.session.commit()


def mco_json():
    return {
        'x': 100,
        'y': 40,
        'problem_id': 1,
        'page': 1,
        'label': 'a',
        'name': 'test'
    }


def fo_json():
    return {
        'name': "fully correct",
        'description': "",
        'score': 4,
        'parent': 12
    }


def fo_child_json():
    return {
        'name': "minor math error",
        'description': "",
        'score': 4,
        'parent': 5
    }


def fo_subchild_json():
    return {
        'name': "integration error",
        'description': '',
        'score': 2
    }


# Actual tests


def test_delete_with_mc_option(test_client, add_test_data):
    """Attempt to delete a FeedbackOption related to a MultipleChoiceOption"""
    req = mco_json()

    result = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(result.data)

    assert data['feedback_id']

    fb_id = data['feedback_id']
    problem_id = 1  # Was inserted in add_test_data()

    result = test_client.delete(f'/api/feedback/{problem_id}/{fb_id}')
    data = json.loads(result.data)

    assert data['status'] == 403


def test_create_and_get_fo(test_client, add_test_data):
    """Create a new FeedbackOption without a parent"""
    fo = fo_json()

    result = test_client.post('/api/feedback/1', data=fo)
    data = json.loads(result.data)
    assert data['name'] == fo['name']
    assert data['description'] == fo['description']
    assert data['score'] == fo['score']

    result_get = test_client.get('/api/feedback/1')
    data_get = json.loads(result_get.data)
    children = data_get['children']
    assert len(children) == 2

    matching_feedback = [feedback for feedback in children if feedback['name'] == 'fully correct']
    assert len(matching_feedback) == 1


def test_create_and_get_fo_with_parent(test_client, add_test_data):
    """Create a new FeedbackOption with a parent"""
    fo_child = fo_child_json()

    result = test_client.post('api/feedback/1', data=fo_child)
    data = json.loads(result.data)
    assert data['parent'] == fo_child['parent']

    result_get = test_client.get('/api/feedback/1')
    data_get = json.loads(result_get.data)
    fbo = data_get['children'][0]['children'][0]
    assert (fbo['name'] == 'minor math error')
    assert (fbo['parent'] == 5)


def test_delete_fo(test_client, add_test_data):
    """Delete a FeedbackOption without a parent"""
    fo = fo_json()

    result_get = test_client.get('/api/feedback/1')
    data_get = json.loads(result_get.data)

    assert len(data_get['children']) == 1

    result = test_client.post('/api/feedback/1', data=fo)
    data = json.loads(result.data)

    assert data['id']

    fb_id = data['id']
    problem_id = 1  # Was inserted in add_test_data()

    result_get = test_client.get('/api/feedback/1')
    data_get = json.loads(result_get.data)

    assert len(data_get['children']) == 2

    result = test_client.delete(f'/api/feedback/{problem_id}/{fb_id}')
    data = json.loads(result.data)

    assert data['status'] == 200

    result_get = test_client.get('/api/feedback/1')
    data_get = json.loads(result_get.data)

    assert len(data_get['children']) == 1


def test_delete_fo_with_parent(test_client, add_test_data):  # Redundant test (serves no purpose)
    """Delete a FeedbackOption with a parent"""
    fo_child = fo_child_json()

    result = test_client.post('/api/feedback/1', data=fo_child)
    data = json.loads(result.data)

    assert data['id']

    fb_id = data['id']
    problem_id = 1  # Was inserted in add_test_data()

    result_get = test_client.get('/api/feedback/1')
    data_get = json.loads(result_get.data)

    assert len(data_get['children']) == 1
    assert len(data_get['children'][0]['children']) == 1

    result = test_client.delete(f'/api/feedback/{problem_id}/{fb_id}')
    data = json.loads(result.data)

    assert data['status'] == 200

    result_get = test_client.get('/api/feedback/1')
    data_get = json.loads(result_get.data)
    assert len(data_get['children']) == 1
    assert len(data_get['children'][0]['children']) == 0


def test_delete_parent_of_fo(test_client, add_test_data):
    """Delete a FeedbackOption with 1 level of children, check if children also get deleted"""
    fo_child = fo_child_json()

    result = test_client.post('/api/feedback/1', data=fo_child)
    data = json.loads(result.data)

    assert data['id']

    problem_id = 1  # Was inserted in add_test_data()

    result_get = test_client.get('/api/feedback/1')
    data_get = json.loads(result_get.data)

    assert len(data_get['children']) == 1
    assert (len(data_get['children'][0]['children']) == 1)

    result = test_client.delete(f'/api/feedback/{problem_id}/5')
    data = json.loads(result.data)

    assert data['status'] == 200

    result_get = test_client.get('/api/feedback/1')
    data_get = json.loads(result_get.data)
    assert len(data_get['children']) == 0


def test_delete_parent_with_subchildren(test_client, add_test_data):
    """Delete a FeedbackOption with 2 levels of children, check if sub-children also get deleted"""
    fo_child = fo_child_json()

    result = test_client.post('/api/feedback/1', data=fo_child)
    data = json.loads(result.data)

    assert data['id']
    parent_id = data['id']

    problem_id = 1  # Was inserted in add_test_data()

    result_get = test_client.get('/api/feedback/1')
    data_get = json.loads(result_get.data)

    assert len(data_get['children']) == 1
    assert len(data_get['children'][0]['children']) == 1

    fo_subchild = fo_subchild_json()
    fo_subchild['parent'] = parent_id

    result = test_client.post('/api/feedback/1', data=fo_subchild)
    data = json.loads(result.data)

    assert data['id']

    result_get = test_client.get('/api/feedback/1')
    data_get = json.loads(result_get.data)

    assert len(data_get['children']) == 1
    fb_p = [feedback for feedback in data_get['children'][0]['children'] if feedback['id'] == parent_id][0]
    assert len(fb_p['children']) == 1

    result = test_client.delete(f'/api/feedback/{problem_id}/5')
    data = json.loads(result.data)

    assert data['status'] == 200

    result_get = test_client.get('/api/feedback/1')
    data_get = json.loads(result_get.data)
    assert len(data_get['children']) == 0


def test_get_children(test_client, add_test_data):
    """Get the children of a FeedbackOption"""
    result = test_client.get('/api/feedback/1')
    data = json.loads(result.data)

    assert len(data['children']) == 1

    fo_p = fo_child_json()

    result = test_client.post('/api/feedback/1', data=fo_p)
    data = json.loads(result.data)

    result = test_client.get("/api/feedback/1")
    data = json.loads(result.data)

    assert len(data['children']) == 1
    assert len(data['children'][0]['children']) == 1

    children = data['children'][0]['children']
    child = children[0]

    assert child['parent'] == 5
