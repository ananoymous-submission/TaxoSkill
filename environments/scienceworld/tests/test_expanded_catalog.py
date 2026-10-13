"""Expanded catalog is opt-in and preserves frozen evaluation tasks."""
import json
import os
from pathlib import Path
import subprocess
import sys


def test_expanded_catalog_is_available_without_replacing_legacy():
    code = """
import json
from scienceworld_env.catalog import get_split, get_task, catalog_sha256
splits = {s: get_split(s) for s in ['development', 'test_seen', 'test_unseen']}
rows = {s: [[t.task_id, t.task_type, t.variation_idx] for t in x.tasks] for s,x in splits.items()}
assert all(get_task(t.task_id) is t for x in splits.values() for t in x.tasks)
print(json.dumps(dict(rows=rows, hashes={s:x.sha256 for s,x in splits.items()}, digest=catalog_sha256())))
"""
    env = dict(os.environ)
    env.pop('SCIENCEWORLD_CATALOG', None)
    legacy = json.loads(subprocess.check_output([sys.executable, '-c', code], env=env, text=True))
    env['SCIENCEWORLD_CATALOG'] = 'find_thermometer_full_v1'
    expanded = json.loads(subprocess.check_output([sys.executable, '-c', code], env=env, text=True))
    assert len(legacy['rows']['development']) == 1483
    assert len(expanded['rows']['development']) == 2490
    assert expanded['digest'] != legacy['digest']
    for split in ['test_seen', 'test_unseen']:
        assert expanded['rows'][split] == legacy['rows'][split]
        assert expanded['hashes'][split] == legacy['hashes'][split]
    dev = expanded['rows']['development']
    heldout = expanded['rows']['test_seen'] + expanded['rows']['test_unseen']
    assert len({tuple(t[1:]) for t in dev}) == len(dev)
    assert not {tuple(t[1:]) for t in dev} & {tuple(t[1:]) for t in heldout}
    assert not {t[0] for t in dev} & {t[0] for t in heldout}
