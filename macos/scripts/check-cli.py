#!/usr/bin/env python3
"""Integration checks against temporary data, never the user's task database."""
import concurrent.futures
import json
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
cli = root / '.build/debug/tasknote'
with tempfile.TemporaryDirectory(prefix='tasknote-check-') as folder:
    db = str(Path(folder) / 'tasks.db')
    def run(*args, ok=True):
        p = subprocess.run([str(cli), '--db', db, *args], capture_output=True, text=True)
        if ok:
            assert p.returncode == 0, p.stderr
            return json.loads(p.stdout)
        assert p.returncode != 0
    run('list')
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        ids = list(pool.map(lambda i: run('add', f'并发任务 {i}')['id'], range(40)))
    assert len(run('list')) == 40
    assert len(set(ids)) == 40
    run('done', ids[0])
    run('rename', ids[0], '更新后的任务')
    assert next(t for t in run('list') if t['id'] == ids[0])['done']
    project = run('project-add', '中文项目', '完成目标', '写一段')['id']
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        actions = list(pool.map(lambda _: run('project-today', project)['id'], range(12)))
    assert len(set(actions)) == 1
    run('done', actions[0])
    assert len(run('project-history', project)) == 1
    assert run('projects')[0]['progress'] == 0
    run('project-set', project, 'progress', '35')
    assert run('projects')[0]['progress'] == 35
    run('project-set', project, 'progress', '101', ok=False)
    run('add', ' ', ok=False)
    run('add', '无效日期', '2026-02-30', ok=False)
    repeat = run('repeat', '每日散步')['id']
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _: run('list'), range(12)))
    assert len([t for t in run('list') if t.get('ruleID') == repeat]) == 1
    print('PASS: CLI JSON, 40 concurrent writes, project dedup, repeat dedup, validation')
