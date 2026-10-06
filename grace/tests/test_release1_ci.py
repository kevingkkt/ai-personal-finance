import importlib.util
import os
from pathlib import Path

import pytest
import requests

BACKEND_URL = os.getenv('SAVINGS_BACKEND_URL', 'http://127.0.0.1:5003')
DATABASE_URL = os.getenv('SAVINGS_DATABASE_URL', 'http://127.0.0.1:6003')
live = pytest.mark.skipif(os.getenv('RUN_SAVINGS_CI_INTEGRATION') != 'true',
                          reason='Requires disposable stack with AI/MCP/RAG disabled')


@live
def test_frontend_available():
    response = requests.get('http://127.0.0.1:3003', timeout=10)
    assert response.status_code == 200
    assert 'Savings Goals' in response.text


@live
@pytest.mark.parametrize('path', ['/ai-insights', '/goals/1/mcp-summary', '/rag-query'])
def test_running_backend_modes_disabled(path):
    response = requests.post(BACKEND_URL + path, json={'query': 'test'}, timeout=10)
    assert response.status_code == 503
    assert response.json()['status'] == 'disabled'


def test_disabled_modes_make_no_external_requests(monkeypatch):
    path = Path(__file__).resolve().parents[1] / 'backend/app.py'
    spec = importlib.util.spec_from_file_location('savings_backend_ci', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.app.config.update(TESTING=True, AI_MODE_ENABLED=False, MCP_ENABLED=False,
                             RAG_ENABLED=False)
    def forbidden(*args, **kwargs):
        raise AssertionError('Disabled mode made an external request')
    monkeypatch.setattr(module.requests, 'get', forbidden)
    monkeypatch.setattr(module.requests, 'post', forbidden)
    async def forbidden_mcp(*args, **kwargs):
        raise AssertionError('Disabled mode invoked MCP')
    monkeypatch.setattr(module, 'invoke_savings_tool', forbidden_mcp)
    client = module.app.test_client()
    for route in ['/ai-insights', '/goals/1/mcp-summary', '/rag-query']:
        response = client.post(route, json={'query': 'test'})
        assert response.status_code == 503
        assert response.json['status'] == 'disabled'


@live
def test_goal_contribution_and_database_integration():
    goal_id = None
    try:
        created = requests.post(f'{BACKEND_URL}/goals', json={
            'goal_name': 'CI temporary savings goal', 'target_amount': 1000,
            'target_date': '31-12-2027'}, timeout=10)
        assert created.status_code == 201
        goal_id = created.json()['id']
        contribution = requests.post(f'{BACKEND_URL}/goals/{goal_id}/contributions', json={
            'amount': 125, 'contribution_date': '28-09-2026'}, timeout=10)
        assert contribution.status_code == 201
        backend = requests.get(f'{BACKEND_URL}/goals/{goal_id}', timeout=10)
        database = requests.get(f'{DATABASE_URL}/goals/{goal_id}', timeout=10)
        assert backend.status_code == database.status_code == 200
        assert backend.json() == database.json()
        assert backend.json()['current_amount'] == 125
    finally:
        if goal_id is not None:
            deleted = requests.delete(f'{BACKEND_URL}/goals/{goal_id}', timeout=10)
            assert deleted.status_code in {200, 204}
