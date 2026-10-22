import importlib.util
from pathlib import Path

import pytest

WORKFLOW_ID = '3f1c2a9e-8b4d-4c6e-9f0a-1b2c3d4e5f60'
GOAL = {'id': 1, 'goal_name': 'Emergency fund', 'target_amount': 1000,
        'current_amount': 250, 'target_date': '31-12-2027'}


class FakeResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise AssertionError(f'Unexpected status {self.status_code}')


@pytest.fixture
def backend(monkeypatch):
    path = Path(__file__).resolve().parents[1] / 'backend/app.py'
    spec = importlib.util.spec_from_file_location('savings_backend_release2', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.app.config.update(TESTING=True, MULTI_AGENT_ENABLED=True)
    module.sent = []

    def fake_get(url, timeout):
        if url.endswith('/goals/1/contributions'):
            return FakeResponse([{'id': 7, 'goal_id': 1, 'amount': 250,
                                  'contribution_date': '01-10-2026'}])
        if url.endswith('/goals/1'):
            return FakeResponse(GOAL)
        if url.endswith('/goals'):
            return FakeResponse([GOAL])
        return FakeResponse({'error': 'Goal not found'}, 404)

    def fake_request(method, url, timeout, **kwargs):
        module.sent.append({'method': method, 'url': url, **kwargs})
        if url.endswith('/multi-agent-history'):
            return FakeResponse([{'task': '[Savings Goal Manager] Review'},
                                 {'task': 'Review Kevin income and expense feature'}])
        return FakeResponse({'workflow_id': WORKFLOW_ID, 'status': 'AWAITING_HUMAN_REVIEW'})

    monkeypatch.setattr(module.requests, 'get', fake_get)
    monkeypatch.setattr(module.requests, 'request', fake_request)
    return module


def test_multi_agent_review_sends_stored_savings_evidence(backend):
    response = backend.app.test_client().post('/multi-agent-review', json={'goal_id': 1})
    assert response.status_code == 200
    sent = backend.sent[0]
    assert sent['url'].endswith('/multi-agent')
    assert sent['json']['task'] == f'{backend.MULTI_AGENT_TAG} {backend.DEFAULT_MULTI_AGENT_TASK}'
    goal = sent['json']['evidence']['goals'][0]
    assert goal['remaining_amount'] == 750
    assert goal['progress_percentage'] == 25.0
    assert goal['contributions'] == [{'amount': 250, 'contribution_date': '01-10-2026'}]


def test_multi_agent_review_covers_all_goals_by_default(backend):
    response = backend.app.test_client().post('/multi-agent-review', json={'task': 'Check goals'})
    assert response.status_code == 200
    payload = backend.sent[0]['json']
    assert payload['task'] == f'{backend.MULTI_AGENT_TAG} Check goals'
    assert [g['goal_id'] for g in payload['evidence']['goals']] == [1]
    assert 'contributions' not in payload['evidence']['goals'][0]


@pytest.mark.parametrize('body, status', [
    ({'goal_id': 'abc'}, 400),
    ({'goal_id': 0}, 400),
    ({'goal_id': True}, 400),
    ({'task': 'x' * 1001}, 400),
    ({'goal_id': 99}, 404),
])
def test_multi_agent_review_rejects_bad_input(backend, body, status):
    response = backend.app.test_client().post('/multi-agent-review', json=body)
    assert response.status_code == status
    assert backend.sent == []


def test_human_review_forwards_decision(backend):
    response = backend.app.test_client().post(
        f'/multi-agent/{WORKFLOW_ID}/human-review',
        json={'decision': 'Partial', 'comments': 'Check the target date'})
    assert response.status_code == 200
    assert backend.sent[0]['url'].endswith(f'/multi-agent/{WORKFLOW_ID}/human-review')
    assert backend.sent[0]['json'] == {'decision': 'partial', 'comments': 'Check the target date'}


@pytest.mark.parametrize('path, body, status', [
    (f'/multi-agent/{WORKFLOW_ID}/human-review', {'decision': 'maybe'}, 400),
    (f'/multi-agent/{WORKFLOW_ID}/human-review', {'decision': 'reject'}, 400),
    ('/multi-agent/not-a-uuid/human-review', {'decision': 'approve'}, 404),
])
def test_human_review_rejects_bad_input(backend, path, body, status):
    response = backend.app.test_client().post(path, json=body)
    assert response.status_code == status
    assert backend.sent == []


def test_history_only_returns_savings_workflows(backend):
    response = backend.app.test_client().get('/multi-agent-history')
    assert response.status_code == 200
    assert response.json == [{'task': '[Savings Goal Manager] Review'}]


def test_multi_agent_disabled_makes_no_external_requests(backend):
    backend.app.config['MULTI_AGENT_ENABLED'] = False
    client = backend.app.test_client()
    for method, path in [('post', '/multi-agent-review'),
                         ('post', f'/multi-agent/{WORKFLOW_ID}/human-review'),
                         ('get', '/multi-agent-history')]:
        response = getattr(client, method)(path, json={'decision': 'approve'})
        assert response.status_code == 503
        assert response.json['status'] == 'disabled'
    assert backend.sent == []


def test_multi_agent_server_down_returns_503(backend, monkeypatch):
    def unreachable(*args, **kwargs):
        raise backend.requests.ConnectionError('refused')
    monkeypatch.setattr(backend.requests, 'request', unreachable)
    response = backend.app.test_client().post('/multi-agent-review', json={})
    assert response.status_code == 503
    assert response.json['error'] == 'Could not connect to Multi-Agent server'
