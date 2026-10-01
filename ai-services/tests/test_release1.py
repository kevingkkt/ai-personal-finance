import asyncio
import importlib.util
import json
from pathlib import Path

import pytest
from mcp import Client

ROOT = Path(__file__).resolve().parents[2]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rag = load_module('rag_under_test', ROOT / 'ai-services/rag_server.py')
mcp = load_module('mcp_under_test', ROOT / 'ai-services/mcp_server.py')
loop = load_module('loop_under_test', ROOT / 'ai-services/shared_agentic_loop.py')


@pytest.fixture
def client(monkeypatch):
    chunk = {'id': 'guide:test:1', 'source': 'savings_goals_guide.md',
             'section': 'Remaining amount', 'version': 'test',
             'text': 'Remaining amount is target amount minus current saved amount.', 'score': .8}
    monkeypatch.setattr(rag, 'retrieve_context', lambda query, feature: [chunk])
    rag.app.config['TESTING'] = True
    return rag.app.test_client()


def test_model_refusal(client, monkeypatch):
    monkeypatch.setattr(rag, 'generate_grounded_answer', lambda *args: {
        'status': 'insufficient_context', 'answer': '', 'source_id': ''})
    response = client.post('/rag', json={'feature': 'savings', 'query': 'Interest rate?'})
    assert response.status_code == 200
    assert response.json['grounded'] is False
    assert response.json['confidence'] == 'Insufficient'
    assert response.json['sources'] == []


def test_empty_answer(client, monkeypatch):
    monkeypatch.setattr(rag, 'generate_grounded_answer', lambda query, chunks: {
        'status': 'answered', 'answer': '', 'source_id': chunks[0]['id']})
    assert client.post('/rag', json={'query': 'Remaining amount?'}).status_code == 502


@pytest.mark.parametrize('source_id,answer', [
    ('guide:test:1', 'Your account earns 12 percent interest.'),
    ('invented', 'Remaining amount is target amount minus current saved amount.'),
])
def test_unsupported_answer(client, monkeypatch, source_id, answer):
    monkeypatch.setattr(rag, 'generate_grounded_answer', lambda *args: {
        'status': 'answered', 'answer': answer, 'source_id': source_id})
    assert client.post('/rag', json={'query': 'Question'}).json['status'] == 'insufficient_context'


def test_supported_quote(client, monkeypatch):
    monkeypatch.setattr(rag, 'generate_grounded_answer', lambda query, chunks: {
        'status': 'answered', 'answer': chunks[0]['text'], 'source_id': chunks[0]['id']})
    data = client.post('/rag', json={'query': 'Remaining amount?'}).json
    assert data['grounded'] is True
    assert data['citations'][0]['quote'] == data['answer']
    assert data['citations'][0]['source_id'] == data['retrieval_evidence'][0]['source_id']


@pytest.mark.parametrize('body', [['invalid'], {'query': 123}, {'query': ''},
                                  {'query': 'x' * 1001}, {'query': 'Q', 'feature': []}])
def test_request_validation(client, body):
    assert client.post('/rag', json=body).status_code == 400


def test_no_retrieval_skips_model(client, monkeypatch):
    monkeypatch.setattr(rag, 'retrieve_context', lambda *args: [])
    def forbidden(*args):
        pytest.fail('Model called without context')
    monkeypatch.setattr(rag, 'generate_grounded_answer', forbidden)
    assert client.post('/rag', json={'query': 'Unknown'}).json['grounded'] is False


def test_real_retrieval_is_feature_scoped():
    chunks = rag.retrieve_context('How is savings progress percentage calculated?', 'savings')
    assert chunks and chunks[0]['section'] == 'Progress percentage'
    assert all(c['source'] == 'savings_goals_guide.md' for c in chunks)
    assert rag.retrieve_context('Who won the FIFA World Cup?', 'savings') == []
    assert rag.retrieve_context('What interest rate will my savings bank pay next year?', 'savings') == []


@pytest.mark.parametrize('target,current,date,status,remaining', [
    (1000, 250, '30-09-2026', 'active', 750),
    (1000, 1250, '27-09-2026', 'completed', 0),
    (1000, 250, '27-09-2026', 'overdue', 750),
    (1000, 250, '28-09-2026', 'due_today', 750),
])
def test_savings_calculation(target, current, date, status, remaining):
    result = mcp.calculate_savings_goal_progress(target, current, date, '28-09-2026')
    assert result['status'] == status
    assert result['remaining_amount'] == remaining
    assert result['progress_percentage'] == current / target * 100


@pytest.mark.parametrize('amount', [float('nan'), float('inf'), -1, 0, 1.001, True, 1000000001])
def test_invalid_money(amount):
    with pytest.raises(ValueError):
        mcp.money_value(amount, 'target', positive=True)


def test_invalid_date():
    with pytest.raises(ValueError):
        mcp.calculate_savings_goal_progress(100, 0, '31-02-2026', '28-09-2026')


def test_real_mcp_protocol_in_memory():
    async def check():
        async with Client(mcp.mcp) as client:
            tools = await client.list_tools()
            assert 'calculate_savings_goal_progress' in {t.name for t in tools.tools}
            result = await client.call_tool('calculate_savings_goal_progress', {
                'target_amount': 1000, 'current_amount': 250,
                'target_date': '30-09-2026', 'reference_date': '28-09-2026'})
            assert not result.is_error
            assert result.structured_content['remaining_amount'] == 750
            invalid = await client.call_tool('calculate_savings_goal_progress', {
                'target_amount': -1, 'current_amount': 250,
                'target_date': '30-09-2026', 'reference_date': '28-09-2026'})
            assert invalid.is_error
            boolean = await client.call_tool('calculate_savings_goal_progress', {
                'target_amount': True, 'current_amount': 0,
                'target_date': '30-09-2026', 'reference_date': '28-09-2026'})
            assert boolean.is_error
    asyncio.run(check())


def test_failed_loop_returns_failure(monkeypatch, tmp_path):
    report = tmp_path / 'report.json'
    monkeypatch.setattr('sys.argv', ['loop', '--mode', 'rag', '--output', str(report)])
    monkeypatch.setattr(loop, 'validate_rag', lambda: False)
    monkeypatch.setattr(loop, 'validate_savings_rag', lambda: True)
    monkeypatch.setattr(loop, 'validate_kevin_rag_backend', lambda: True)
    assert loop.main() == 1
    assert json.loads(report.read_text())['passed'] is False
