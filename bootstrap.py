"""Windows recovery commands using standard Python only.

BOOT-NATIVE: Fresh config names native coding; only same-root legacy ownership
keys survive reconfiguration, including historical input/decoder identity when
root is absent. Matching roots reject malformed ownership before any writes;
conflicting identity never carries ownership. Evidence: tests/test_native_migration.py.
BOOT-1: Generate machine-local config and provision manifests from relative,
hash-pinned catalog entries. Reject absolute/traversal destinations and preserve
existing config in a private backup before replacing it.
BOOT-2: Downloads/installation/model alias changes require explicit --approved.
Reject pinned-base digest drift and back up existing aliases before replacing.
BOOT-3: Comfy installation uses pinned source/runtime locks and refuses to
modify a pre-existing unrelated application or Python environment. Running it
uses argv without a shell, loopback8189, offline mode and reserve-vram3.5.
BOOT-4: Verification reports doctor readiness and decoder imports without submitting jobs.
BOOT-2: Stage under a unique alias. Before copying to the live alias, persist its
old and intended digests under the shared GPU lease. Only an acknowledged copy
plus digest verification clears the guard. Unknown outcomes retain backup and
candidate for operator reconciliation after draining pending Ollama operations.
BOOT-3: Reuse and launch require an unchanged tracked core at the pinned commit.
Inspect ignored and other untracked overrides, including custom nodes. Permit
catalog code only at its exact digest. Preserve model data and operator files.
Evidence: tests/test_bootstrap.py and tests/test_bootstrap_install.py use temporary
directories and simulated services; they do not prove fresh-OS setup.
"""
from pathlib import Path, PureWindowsPath
import argparse
import hashlib
import http.client
import json
import ntpath
import os
import re
import shutil
import subprocess
import sys
import uuid

import harness
import provision

BASE = Path(__file__).resolve().parent


def expand_destination(item, roots):
    selector = item.get('destination_root')
    root = roots.get(selector)
    value = item.get('destination')
    if root is None or not isinstance(value, str):
        raise ValueError('Catalog entry needs a known destination root and relative destination')
    for part in value.split('/'):
        reserved = ntpath.isreserved(part) if hasattr(ntpath, 'isreserved') else PureWindowsPath(part).is_reserved()
        if (not part or part in ('.', '..') or part.endswith((' ', '.')) or reserved
                or re.search(r'[<>:"\\|?*\x00-\x1f]', part)):
            raise ValueError('Unsafe catalog destination: ' + value)
    destination = (root / value).resolve()
    if not destination.is_relative_to(root):
        raise ValueError('Catalog destination escapes its root: ' + value)
    return dict(item, destination=str(destination))


def configure(comfy_root, base=BASE):
    """BOOT-1: Validate the complete portable catalog before writing local paths."""
    base = Path(base).resolve()
    root = Path(comfy_root).expanduser().resolve()
    app = root / 'app'
    downloads = base / 'work' / 'downloads'
    if app.resolve() != app or downloads.resolve() != downloads:
        raise ValueError('Application and downloads roots must not be redirected')
    catalog = harness.read_json(base/'manifests/catalog.json')
    if catalog.get('schema_version') != 1:
        raise ValueError('Unsupported catalog schema')
    roots = {'comfy': app, 'downloads': downloads}
    manifest = dict(catalog, comfy_root=str(app))
    for group in ('files', 'python_packages'):
        manifest[group] = [expand_destination(item, roots) for item in catalog[group]]
        for item in manifest[group]:
            if not re.fullmatch('[a-f0-9]{64}', item.get('sha256') or ''):
                raise ValueError('Catalog entry lacks a SHA-256 pin: '+item['destination'])
    if catalog.get('voice_assembly'):
        manifest['voice_assembly'] = expand_destination(catalog['voice_assembly'], roots)
    manifest_path = downloads.parent / 'download-manifest.json'
    provision.validate_manifest(manifest, manifest_path)
    config = {'coding': {'coder':'terra_coder', 'model':'gpt-6.1-terra', 'provider':'openai', 'reviewer':'terra'},
              'comfy_url': 'http://127.0.0.1:8189', 'comfy_root': str(app),
              'comfy_input_dir': str(app/'input'), 'decoder_python': str(root/'python/Scripts/python.exe')}
    config_path = base/'config.json'
    if config_path.exists():
        old = harness.read_json(config_path)
        identities = {'comfy_root': app, 'comfy_input_dir': app/'input',
                      'decoder_python': root/'python/Scripts/python.exe'}
        def matches(key):
            value = old.get(key)
            return isinstance(value, str) and bool(value) and Path(value).expanduser().resolve() == identities[key]
        if 'comfy_root' in old:
            same_root = matches('comfy_root') and all(matches(k) for k in ('comfy_input_dir','decoder_python') if k in old)
        else:
            same_root = matches('comfy_input_dir') and matches('decoder_python')
        if same_root:
            harness.validate_legacy_handoff(old)
            if 'model' in old:
                config.update(model=old['model'], ollama_url=old['ollama_url'])
    if config_path.exists() and config_path.read_bytes() != json.dumps(config, indent=2).encode():
        backup = base/'.runtime'/('config-backup-'+uuid.uuid4().hex+'.json')
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(config_path, backup)
    harness.write_json(manifest_path, manifest)
    harness.write_json(config_path, config)
    return {'config': str(config_path), 'manifest': str(manifest_path)}


def require_approval(approved):
    if not approved:
        raise PermissionError('Pass --approved before downloading or modifying an installation')


def ollama_request(endpoint, payload=None, method=None):
    """BOOT-2: Direct loopback HTTP, bounded JSON and no redirect or proxy."""
    connection = http.client.HTTPConnection('127.0.0.1', 11434, timeout=7200 if endpoint == 'pull' else 120)
    try:
        body = json.dumps(payload).encode() if payload is not None else None
        connection.request(method or ('GET' if body is None else 'POST'), '/api/'+endpoint,
                           body, {'Content-Type': 'application/json'})
        response = connection.getresponse()
        limit = 4 * 1024 * 1024
        data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError('Ollama '+endpoint+' response exceeds 4 MiB')
        if not 200 <= response.status < 300:
            raise ValueError(f'Ollama {endpoint} returned HTTP {response.status}: '+data[:2048].decode(errors='replace'))
        if not data.strip():
            if endpoint in ('copy', 'delete'):
                return {}
            raise ValueError('Ollama '+endpoint+' returned an empty response')
        result = json.loads(data)
        if not isinstance(result, dict) or result.get('error'):
            raise ValueError(f'Invalid Ollama {endpoint} response: {str(result)[:2048]}')
        return result
    except (OSError, http.client.HTTPException) as error:
        raise OSError(f'Ollama {endpoint} at 127.0.0.1:11434 failed: {error}') from error
    finally:
        connection.close()


def digest(value):
    value = value.removeprefix('sha256:') if isinstance(value, str) else ''
    if not re.fullmatch('[a-f0-9]{64}', value):
        raise ValueError('Invalid Ollama model digest')
    return value


def installed_models():
    return {row['name']: digest(row['digest']) for row in ollama_request('tags')['models']}


def verify_context(worker, context):
    params = ollama_request('show', {'model': worker}).get('parameters', '')
    if not re.search(r'(?m)^\s*num_ctx\s+'+str(context)+r'\s*$', params):
        raise ValueError(f'Ollama {worker} does not report num_ctx {context}')


def setup_ollama(approved=False, base=BASE):
    """BOOT-2: Check content identity before changing aliases. Retain a verified backup."""
    require_approval(approved)
    lease = harness.GpuLease(Path(base)/'.runtime')
    if not lease.acquire():
        raise RuntimeError('The local harness is busy; retry when its job or setup finishes')
    try:
        return configure_alias(harness.read_json(Path(base)/'locks/runtime.json')['ollama'], lease.unconfirmed_alias)
    finally:
        lease.release()


def configure_alias(lock, guard):
    source, worker, context = lock['base_model'], lock['worker_model'], lock['context_length']
    expected = digest(lock['base_digest'])
    if source == worker or type(context) is not int or context <= 0:
        raise ValueError('Invalid worker alias or context lock')
    models = installed_models()
    if source not in models:
        if ollama_request('pull', {'model': source, 'stream': False}).get('status') != 'success':
            raise ValueError('Ollama pull did not return success')
        models = installed_models()
    if models.get(source) != expected:
        raise ValueError(f'Base digest mismatch for {source}: expected {expected}, got {models.get(source)}')
    previous = models.get(worker)
    if previous and lock.get('worker_digest') and previous == digest(lock['worker_digest']):
        verify_context(worker, context)
        return {'model': worker, 'reused': True}
    candidate = worker+'-setup-'+uuid.uuid4().hex
    backup = None
    try:
        created = ollama_request('create', {'model': candidate, 'from': source,
                                'parameters': {'num_ctx': context}, 'stream': False})
        if created.get('status') != 'success':
            raise ValueError('Ollama create did not return success')
        verify_context(candidate, context)
        current = installed_models()
        candidate_digest = current.get(candidate)
        if current.get(source) != expected or not candidate_digest:
            raise ValueError('Base or candidate digest changed or disappeared during setup')
        if current.get(worker) != previous:
            raise ValueError('Worker changed while creating candidate; preserving current worker')
        if previous != candidate_digest:
            if previous:
                backup = worker+'-backup-'+uuid.uuid4().hex
                ollama_request('copy', {'source': worker, 'destination': backup})
                if installed_models().get(backup) != previous:
                    raise ValueError('Worker backup digest mismatch. Preserved the existing alias')
            harness.write_json(guard, {'worker': worker, 'previous_digest': previous,
                                       'candidate': candidate, 'candidate_digest': candidate_digest,
                                       'backup': backup})
            ollama_request('copy', {'source': candidate, 'destination': worker})
            if installed_models().get(worker) != candidate_digest:
                raise ValueError('Promoted worker digest differs from the verified candidate')
            guard.unlink()
    except (Exception, KeyboardInterrupt) as error:
        if os.path.lexists(guard):
            raise RuntimeError(f'{error}. Live alias promotion requires operator reconciliation: {guard}') from error
        try:
            if candidate in installed_models():
                ollama_request('delete', {'model': candidate}, 'DELETE')
        except Exception as recovery:
            raise RuntimeError(f'{error}. Recovery failed: {recovery}. Backup: {backup}. Candidate: {candidate}') from error
        raise
    ollama_request('delete', {'model': candidate}, 'DELETE')
    return {'model': worker, 'digest': candidate_digest, 'backup': backup, 'reused': previous == candidate_digest}


def install_comfy(approved=False, base=BASE):
    """BOOT-3: Create both paths exclusively. Matching receipts permit read-only reuse.

    Failed new components are retained under a unique sibling for inspection.
    Existing components with missing or mismatched receipts are never repaired in place.
    """
    require_approval(approved)
    base = Path(base)
    config = harness.read_json(base/'config.json')
    app = Path(config['comfy_root'])
    venv = app.parent/'python'
    python = venv/'Scripts/python.exe'
    if app.name != 'app' or app.resolve() != app or venv.resolve() != venv or Path(config['decoder_python']) != python:
        raise ValueError('Configured install paths are inconsistent or redirected; run configure again')
    lock = harness.read_json(base/'locks/runtime.json')['comfyui']
    if not re.fullmatch(r'[0-9a-f]{40}', lock['commit']) or not lock['repository'].startswith('https://'):
        raise ValueError('ComfyUI requires a full pinned Git commit and HTTPS repository')
    requirements = base/'locks/comfy-requirements.txt'
    env_lock = {'comfy_requirements_sha256': hashlib.sha256(requirements.read_bytes()).hexdigest(),
                'python': '3.12', 'path': str(venv)}
    marker = '.codex-comfy-bootstrap.json'
    for path, receipt in ((app, lock), (venv, env_lock)):
        if os.path.lexists(path):
            if not (path/marker).is_file():
                raise ValueError(f'Preserving existing {path}: missing ownership receipt')
            if harness.read_json(path/marker) != receipt:
                raise ValueError(f'Preserving {path}: ownership receipt or lock mismatch')
    if venv.exists() and not python.is_file():
        raise ValueError(f'Existing owned environment lacks {python}')
    if not venv.exists() and sys.version_info[:2] != (3, 12):
        raise ValueError('Use 64-bit Python 3.12 to install ComfyUI: py -3.12 bootstrap.py comfy --approved')
    if not app.exists():
        app.mkdir(parents=True)
        try:
            for argv in (['git','init'], ['git','fetch','--depth','1',lock['repository'],lock['commit']],
                         ['git','checkout','--detach',lock['commit']]):
                subprocess.run(argv, cwd=app, check=True)
            harness.write_json(app/marker, lock)
        except (Exception, KeyboardInterrupt):
            app.rename(app.with_name('app-failed-'+uuid.uuid4().hex))
            raise
    check_core(app, lock, base)
    if not venv.exists():
        venv.mkdir()
        try:
            subprocess.run([sys.executable,'-m','venv',str(venv)], check=True)
            subprocess.run([str(python),'-m','pip','--isolated','install','--require-hashes',
                            '--only-binary=:all:','-r',str(requirements)], check=True)
            harness.write_json(venv/marker, env_lock)
        except (Exception, KeyboardInterrupt):
            venv.rename(venv.with_name('python-failed-'+uuid.uuid4().hex))
            raise
    return {'app': str(app), 'python': str(python), 'commit': lock['commit']}


def check_core(app, lock, base):
    """BOOT-3: Read Git's tracked state and include ignored files in the override scan.

    The provisioner owns model-content validation. Only catalog source files are hashed
    here. The foreground launcher disables bytecode writes to keep managed source clean.
    """
    def git(*args):
        return subprocess.run(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false',
                               *args], cwd=app, check=True, capture_output=True,
                              text=True, encoding='utf-8').stdout

    if git('rev-parse', 'HEAD').strip() != lock['commit'] or not (app/'main.py').is_file():
        raise ValueError('ComfyUI checkout does not match the locked application')
    if git('status', '--porcelain=v1', '--untracked-files=no', '--ignore-submodules=none').strip():
        raise ValueError('Preserving changed tracked ComfyUI sources')
    catalog = harness.read_json(Path(base)/'manifests/catalog.json')
    allowed = {row['destination']: row for row in catalog['files'] if row['destination_root'] == 'comfy'}
    voices = (catalog.get('voice_assembly') or {}).get('destination')
    executable = {'.py', '.pyc', '.pyo', '.pyw', '.pyd', '.pth', '.dll', '.so', '.exe',
                  '.ps1', '.cmd', '.bat', '.js', '.mjs', '.zip', '.whl'}
    for entry in git('ls-files', '--cached', '--others', '-v', '-z').split('\0'):
        if not entry:
            continue
        tag, relative = entry.split(' ', 1)
        if tag == 'S' or tag.islower():
            raise ValueError('Cannot verify hidden tracked ComfyUI source: '+relative)
        if tag != '?':
            continue
        path = app/relative
        custom_node = relative.casefold().startswith('custom_nodes/')
        if (not custom_node and path.suffix.lower() not in executable
                and path.name.lower() != 'extra_model_paths.yaml'
                and not relative.endswith('/') and path.resolve() == path):
            continue
        if path.resolve() != path:
            raise ValueError('Unexpected untracked redirected path: '+relative)
        row = allowed.get(relative)
        if row and row['purpose'] == 'speech-node':
            if path.stat().st_size != row['size_bytes'] or provision.digest(path) != row['sha256']:
                raise ValueError('Custom node source digest mismatch: '+relative)
        elif not (custom_node and path.suffix.lower() not in executable and
                  (relative == voices or (row and row['purpose'] == 'speech-model'))):
            raise ValueError('Unexpected untracked ComfyUI code or custom node: '+relative)


def run_comfy(base=BASE):
    """BOOT-3: Run the configured decoder and app in the foreground."""
    config = harness.read_json(Path(base)/'config.json')
    app = Path(config['comfy_root'])
    check_core(app, harness.read_json(Path(base)/'locks/runtime.json')['comfyui'], base)
    subprocess.run([config['decoder_python'],'-B',str(app/'main.py'),'--listen','127.0.0.1',
                    '--port','8189','--reserve-vram','3.5','--offline'], cwd=app, check=True)
    return {'state': 'stopped'}


def verify(base=BASE):
    """BOOT-4: Doctor inspects services and templates; import-check the configured decoder."""
    config = harness.read_json(Path(base)/'config.json')
    result = harness.doctor(config)
    try:
        subprocess.run([config['decoder_python'],'-I','-c','import av; from PIL import Image'],
                              check=True, capture_output=True, text=True, timeout=60)
        result['decoder'] = {'ready': True, 'python': config['decoder_python']}
    except (OSError, subprocess.SubprocessError) as error:
        result['decoder'] = {'ready': False, 'error': (getattr(error,'stderr',None) or str(error)).strip()}
    result['ready'] = result['ready'] and result['decoder']['ready']
    result['scope'] = 'Service metadata, preset dependencies and decoder imports. No inference or generation submitted.'
    return result


def main(argv=None, base=BASE):
    parser = argparse.ArgumentParser(description='Configure and recover the local Windows harness')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('configure').add_argument('--comfy-root', required=True, type=Path)
    for name in ('comfy','models','ollama'):
        commands.add_parser(name).add_argument('--approved', action='store_true')
    commands.add_parser('verify')
    commands.add_parser('run-comfy')
    args = parser.parse_args(argv)
    try:
        if args.command == 'configure':
            result = configure(args.comfy_root, base)
        elif args.command == 'models':
            require_approval(args.approved)
            result = provision.provision(Path(base)/'work/download-manifest.json', approved=args.approved)
        elif args.command == 'comfy':
            result = install_comfy(args.approved, base)
        elif args.command == 'ollama':
            result = setup_ollama(args.approved, base)
        elif args.command == 'run-comfy':
            result = run_comfy(base)
        else:
            result = verify(base)
        print(json.dumps(result, indent=2))
        return 1 if result.get('ready') is False else 0
    except (KeyError, ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
