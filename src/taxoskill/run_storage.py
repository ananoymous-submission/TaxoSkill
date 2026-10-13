"""Explicit omission-scoped storage; seeds and shared partitions stay separate."""
from pathlib import Path
import json
import math
from decimal import Decimal

CONDITIONS = ('no_skill', 'global_random', 'global_taxoskill', 'per_cluster_taxoskill')


def run_name(condition: str, seed: int) -> str:
    if condition not in CONDITIONS:
        raise ValueError(f'unknown run condition: {condition}')
    if type(seed) is not int or seed < 0:
        raise ValueError('seed must be a non-negative integer')
    return f'{condition}_seed_{seed}'


def path_component(value: str) -> str:
    if not value.strip() or value in {'.', '..'} or '/' in value or '\\' in value:
        raise ValueError(f'expected a single non-empty path component, got {value!r}')
    return value


def target_label(target: float) -> str:
    """Canonical decimal target label, not the achieved pool statistic."""
    if isinstance(target, bool) or not isinstance(target, (int, float)) or not math.isfinite(target) or not 0 <= target <= 1:
        raise ValueError('target must be a finite number in [0, 1]')
    value = format(Decimal(str(target)), 'f')
    whole, _, fraction = value.partition('.')
    return whole + '.' + fraction.rstrip('0').ljust(2, '0')


def seeded_root(root: Path, environment: str, seed: int, *, omission: float | None = None) -> Path:
    if type(seed) is not int or seed < 0:
        raise ValueError('seed must be a non-negative integer')
    base = root / path_component(environment)
    if omission is not None:
        base /= f'omission_{target_label(omission)}'
    return base / f'seed_{seed}'


def skillopt_root(environment: str, seed: int, *, omission: float | None = None) -> Path:
    return seeded_root(Path('outputs/skillopt'), environment, seed, omission=omission)


def seeded_skill_output(path: Path, environment: str, seed: int, *, omission: float | None = None) -> Path:
    """Scope an explicit split destination; never write into another seed."""
    base = Path('outputs/skillopt') / path_component(environment)
    scoped = skillopt_root(environment, seed, omission=omission)
    relative = path.resolve().relative_to(base.resolve())
    if not relative.parts:
        raise ValueError('split output must name a directory within the environment')
    if relative.parts[0].startswith('omission_'):
        if omission is None or relative.parts[0] != scoped.parent.name:
            raise ValueError('split output condition differs from configuration omission')
        relative = Path(*relative.parts[1:])
        if not relative.parts:
            raise ValueError('split output must name a run within the condition')
    if relative.parts[0].startswith('seed_'):
        if relative.parts[0] != scoped.name:
            raise ValueError('split output seed differs from configuration seed')
        if len(relative.parts) == 1:
            raise ValueError('split output must name a run within the seed')
        return scoped.parent / relative
    return scoped / relative


def validate_artifact_scope(directory: Path, *, environment: str, seed: int,
                            repeat: int | None = None, omission: float | None = None) -> None:
    """Reject cross-condition/seed artifacts; new condition-scoped artifacts require provenance."""
    seeded_root(Path('.'), environment, seed, omission=omission)
    candidates = (directory / 'resolved_config.json', directory / 'split.json')
    metadata = next((path for path in candidates if path.is_file()), None)
    if metadata is None:
        if omission is not None:
            raise ValueError(f'condition-scoped artifact has no scope metadata: {directory}')
        return
    source = json.loads(metadata.read_text(encoding='utf-8'))
    if source.get('seed') != seed:
        raise ValueError(f'artifact seed differs from configuration seed: {metadata}')
    if source.get('omission') != omission:
        raise ValueError(f'artifact omission differs from configuration omission: {metadata}')
    source_env = source.get('env', {}).get('name', source.get('environment'))
    if source_env != environment and (source_env is not None or omission is not None):
        raise ValueError(f'artifact environment differs from configuration: {metadata}')
    if repeat is not None and source.get('evaluation', {}).get('repeat') != repeat:
        raise ValueError(f'artifact repeat differs from configuration repeat: {metadata}')
