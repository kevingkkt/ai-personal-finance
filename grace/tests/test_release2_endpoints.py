"""Release 2 post-commit CI tests for two Savings Goals backend endpoints.

Endpoint 1: GET  /goals                         (list savings goals)
Endpoint 2: POST /goals/<goal_id>/contributions (add a contribution to a goal)

These run against the disposable Docker stack started by .github/workflows/Grace.yml.
"""
import os

import pytest
import requests

BACKEND_URL = os.getenv('SAVINGS_BACKEND_URL', 'http://127.0.0.1:5003')
DATABASE_URL = os.getenv('SAVINGS_DATABASE_URL', 'http://127.0.0.1:6003')
GOAL_FIELDS = {'id', 'goal_name', 'target_amount', 'current_amount', 'target_date'}

pytestmark = pytest.mark.skipif(
    os.getenv('RUN_SAVINGS_CI_INTEGRATION') != 'true',
    reason='Requires the disposable savings stack started by Grace CI')


@pytest.fixture
def temporary_goal():
    created = requests.post(f'{BACKEND_URL}/goals', json={
        'goal_name': 'CI endpoint test goal', 'target_amount': 1000,
        'target_date': '31-12-2027'}, timeout=10)
    assert created.status_code == 201
    goal = created.json()
    yield goal
    requests.delete(f'{BACKEND_URL}/goals/{goal["id"]}', timeout=10)


# Endpoint 1: GET /goals

def test_get_goals_endpoint(temporary_goal):
    response = requests.get(f'{BACKEND_URL}/goals', timeout=10)

    assert response.status_code == 200
    goals = response.json()
    assert isinstance(goals, list)
    assert all(GOAL_FIELDS.issubset(goal) for goal in goals)
    listed = next(goal for goal in goals if goal['id'] == temporary_goal['id'])
    assert listed['goal_name'] == 'CI endpoint test goal'
    assert listed['current_amount'] == 0

    # The backend returns exactly what the database service stores.
    database = requests.get(f'{DATABASE_URL}/goals', timeout=10)
    assert database.status_code == 200
    assert goals == database.json()


# Endpoint 2: POST /goals/<goal_id>/contributions

def test_create_contribution_endpoint(temporary_goal):
    goal_id = temporary_goal['id']
    response = requests.post(f'{BACKEND_URL}/goals/{goal_id}/contributions', json={
        'amount': 125.5, 'contribution_date': '01-10-2026'}, timeout=10)

    assert response.status_code == 201
    contribution = response.json()
    assert contribution['goal_id'] == goal_id
    assert contribution['amount'] == 125.5
    assert contribution['contribution_date'] == '01-10-2026'

    # The goal's saved amount is updated from its contributions.
    goal = requests.get(f'{BACKEND_URL}/goals/{goal_id}', timeout=10).json()
    assert goal['current_amount'] == 125.5


@pytest.mark.parametrize('body, status', [
    ({'amount': 0, 'contribution_date': '01-10-2026'}, 400),
    ({'amount': 'abc', 'contribution_date': '01-10-2026'}, 400),
    ({'amount': 50, 'contribution_date': '2026-10-01'}, 400),
])
def test_create_contribution_endpoint_rejects_invalid_input(temporary_goal, body, status):
    goal_id = temporary_goal['id']
    response = requests.post(f'{BACKEND_URL}/goals/{goal_id}/contributions',
                             json=body, timeout=10)

    assert response.status_code == status
    goal = requests.get(f'{BACKEND_URL}/goals/{goal_id}', timeout=10).json()
    assert goal['current_amount'] == 0


def test_create_contribution_endpoint_unknown_goal():
    response = requests.post(f'{BACKEND_URL}/goals/999999/contributions', json={
        'amount': 10, 'contribution_date': '01-10-2026'}, timeout=10)

    assert response.status_code == 404
