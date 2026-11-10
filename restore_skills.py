"""Restore the recorded standalone skills without replacing an existing skill.

SKILLS-1: Preview without approval is read-only. Approved restore verifies pinned
source files and bundled custom files before publishing any skill under the
selected profile's .agents/skills. Matching installs are idempotent; conflicts,
including legacy .codex/skills, are preserved with an error.
SKILLS-2: Reject unsafe Windows paths, duplicate names, redirected paths and
digest mismatches before destination writes. Fetch only pinned public GitHub
revisions, without executing skill scripts. Never copy plugin caches or secrets.
SKILLS-3: Plugin restore is separate and opt-in, delegates installation to the
Codex CLI with the selected CODEX_HOME, preserves enabled plugins, and reports
each failed command. Preserve registered matching marketplaces; reject a same-name
source/ref conflict before invoking Codex. Account connections remain manual.
Evidence: tests/test_restore_skills.py uses real temporary files and a fake
source fetch; live restore evidence is recorded separately in TDD_EVIDENCE.md.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import sys
import tomllib

BASE = Path(__file__).resolve().parent


def safe_path(value, single=False):
    if not isinstance(value, str) or not value or '\\' in value:
        raise ValueError('Unsafe skill path')
    parts = value.split('/')
    reserved = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)),
                *(f'LPT{i}' for i in range(1, 10))}
    if (single and len(parts) != 1) or any(
        part in ('', '.', '..', '.git') or part[-1:] in (' ', '.') or
        re.search(r'[<>:"|?*\x00-\x1f]', part) or
        part.split('.')[0].upper() in reserved for part in parts
    ):
        raise ValueError('Unsafe skill path: '+value)
    return Path(*parts)


def no_redirect(path):
    for parent in (path, *path.parents):
        if parent.exists() or parent.is_symlink():
            info = parent.lstat()
            if parent.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise ValueError('Redirected skill path: '+str(parent))


def canonical(data, row):
    if row.get('normalize_lf'):
        data = data.decode('utf-8').replace('\r\n', '\n').encode('utf-8')
    return data


def fetch_source(source, destination, paths):
    destination.mkdir()
    def git(*args):
        subprocess.run(['git', '-c', 'core.hooksPath='+str(destination/'disabled-hooks'),
                        '-c', 'core.fsmonitor=false', *args], cwd=destination,
                       check=True, capture_output=True, text=True, timeout=600)
    git('init', '--quiet')
    git('config', 'core.autocrlf', 'false')
    git('config', 'core.symlinks', 'false')
    git('remote', 'add', 'origin', 'https://github.com/'+source['repo']+'.git')
    git('fetch', '--quiet', '--depth=1', 'origin', source['commit'])
    if '.' not in paths:
        git('sparse-checkout', 'set', '--cone', '--', *sorted(paths))
    git('checkout', '--quiet', '--detach', source['commit'])
    return destination


def restore(manifest, codex_home, approved=False, base=None):
    base = Path(base or BASE).absolute()
    home = Path(codex_home).absolute()
    destination = home.parent/'.agents/skills'
    sources = {}
    for source in manifest['sources']:
        if (source['id'] in sources or not re.fullmatch(r'[\w.-]+/[\w.-]+', source['repo'])
                or not re.fullmatch(r'[0-9a-f]{40}', source['commit'])):
            raise ValueError('Invalid or duplicate pinned skill source')
        sources[source['id']] = source
    names = set()
    for skill in manifest['skills']:
        safe_path(skill['name'], single=True)
        if skill['name'].casefold() in names or skill['name'].casefold() == 'local-harness':
            raise ValueError('Duplicate or generated skill name: '+skill['name'])
        names.add(skill['name'].casefold())
        if 'source' in skill and skill['source'] not in sources:
            raise ValueError('Unknown skill source')
        if skill.get('path', '.') != '.': safe_path(skill['path'])
        paths = set()
        if 'SKILL.md' not in skill['files']: raise ValueError('Missing SKILL.md')
        for relative, row in skill['files'].items():
            safe_path(relative)
            if relative.casefold() in paths: raise ValueError('Duplicate skill file path')
            paths.add(relative.casefold())
            if ('local' not in row and 'source' not in skill or
                    not re.fullmatch(r'[0-9a-f]{64}', row['sha256']) or
                    not isinstance(row['size_bytes'], int) or row['size_bytes'] < 0):
                raise ValueError('Invalid skill file record')
            if 'local' in row: safe_path(row['local'])
    result = {'state': 'preview', 'destination': str(destination),
              'skills': [skill['name'] for skill in manifest['skills']],
              'files': sum(len(skill['files']) for skill in manifest['skills']),
              'size_bytes': sum(row['size_bytes'] for skill in manifest['skills'] for row in skill['files'].values())}
    if not approved:
        return result
    no_redirect(home)
    no_redirect(destination)
    work = base/'work'
    work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='skills-sources-', dir=work) as scratch:
        fetched = {}
        payloads = {}
        for skill in manifest['skills']:
            payload = {}
            for relative, row in skill['files'].items():
                if 'local' in row:
                    path = base/safe_path(row['local'])
                else:
                    key = skill['source']
                    if key not in fetched:
                        paths = {s.get('path', '.') for s in manifest['skills'] if s.get('source') == key}
                        fetched[key] = fetch_source(sources[key], Path(scratch)/str(len(fetched)), paths)
                    path = fetched[key]/skill.get('path', '.')/safe_path(relative)
                no_redirect(path)
                data = canonical(path.read_bytes(), row)
                if len(data) != row['size_bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
                    raise ValueError('Skill digest mismatch: '+skill['name']+'/'+relative)
                payload[relative] = data
            payloads[skill['name']] = payload
        installed, unchanged = [], []
        for skill in manifest['skills']:
            name = skill['name']
            for target in (destination/name, home/'skills'/name):
                no_redirect(target)
                if not target.exists(): continue
                if not target.is_dir(): raise ValueError('Skill conflict: '+str(target))
                actual = {}
                for path in target.rglob('*'):
                    no_redirect(path)
                    if path.is_file():
                        relative = path.relative_to(target).as_posix()
                        actual[relative] = canonical(path.read_bytes(), skill['files'].get(relative, {}))
                if actual != payloads[name]:
                    raise ValueError('Skill conflict, preserving existing files: '+str(target))
            if (destination/name).exists(): unchanged.append(name)
            else: installed.append(name)
        # Stage on the destination volume so publication is a directory rename.
        destination.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.harness-skills-', dir=destination) as staging:
            for name in installed:
                target = Path(staging)/name
                target.mkdir()
                for relative, data in payloads[name].items():
                    path = target/safe_path(relative)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
            for name in installed:
                target = destination/name
                no_redirect(target)
                if target.exists(): raise ValueError('Skill conflict during publication: '+str(target))
                (Path(staging)/name).rename(target)
    result.update(state='installed', installed=installed, unchanged=unchanged)
    return result


def restore_plugins(manifest, codex_home, approved=False):
    home = Path(codex_home).absolute()
    no_redirect(home)
    for plugin in manifest['plugins']:
        if not re.fullmatch(r'[\w.-]+@[\w.-]+', plugin):
            raise ValueError('Invalid plugin identifier')
    for marketplace in manifest['marketplaces']:
        if (not re.fullmatch(r'[\w.-]+', marketplace['name']) or
                not re.fullmatch(r'[\w.-]+/[\w.-]+', marketplace['source']) or
                not re.fullmatch(r'[0-9a-f]{40}', marketplace['ref'])):
            raise ValueError('Invalid pinned plugin marketplace')
    result = {'state': 'preview', 'plugins': manifest['plugins'],
              'marketplaces': manifest['marketplaces']}
    if not approved: return result
    config = home/'config.toml'
    no_redirect(config)
    settings = tomllib.loads(config.read_text(encoding='utf-8-sig')) if config.exists() else {}
    enabled = settings.get('plugins', {})
    registered = settings.get('marketplaces', {})
    for marketplace in manifest['marketplaces']:
        existing = registered.get(marketplace['name'])
        if existing is None: continue
        source = existing.get('source', '').removeprefix('https://github.com/').removesuffix('.git').rstrip('/')
        if (existing.get('source_type') != 'git' or source.casefold() != marketplace['source'].casefold()
                or existing.get('ref') not in (None, marketplace['ref'])):
            raise ValueError('Plugin marketplace conflict, preserving existing settings: '+marketplace['name'])
    home.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, CODEX_HOME=str(home))
    installed, unchanged, failed = [], [], []
    def run(*args):
        subprocess.run(['codex', 'plugin', *args, '--json'], env=environment,
                       check=True, capture_output=True, text=True, timeout=600)
    for marketplace in manifest['marketplaces']:
        if marketplace['name'] in registered: continue
        try:
            run('marketplace', 'add', marketplace['source'], '--ref', marketplace['ref'])
        except (OSError, subprocess.SubprocessError) as error:
            failed.append({'marketplace': marketplace['source'],
                           'error': (getattr(error, 'stderr', None) or str(error)).strip()})
    for plugin in manifest['plugins']:
        if enabled.get(plugin, {}).get('enabled') is True:
            unchanged.append(plugin)
            continue
        try:
            run('add', plugin)
            installed.append(plugin)
        except (OSError, subprocess.SubprocessError) as error:
            failed.append({'plugin': plugin,
                           'error': (getattr(error, 'stderr', None) or str(error)).strip()})
    result.update(state='incomplete' if failed else 'installed',
                  installed=installed, unchanged=unchanged, failed=failed)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--approved', action='store_true', help='Fetch and install the recorded skills')
    parser.add_argument('--plugins', action='store_true', help='Restore recorded plugins instead of standalone skills')
    parser.add_argument('--codex-home', type=Path, default=Path(os.environ.get('CODEX_HOME', Path.home()/'.codex')))
    args = parser.parse_args(argv)
    try:
        manifest = json.loads((BASE/'manifests'/('plugins.json' if args.plugins else 'skills.json')).read_text(encoding='utf-8'))
        result = (restore_plugins(manifest, args.codex_home, args.approved) if args.plugins else
                  restore(manifest, args.codex_home, args.approved))
        print(json.dumps(result, indent=2))
        return 1 if result['state'] == 'incomplete' else 0
    except (KeyError, TypeError, ValueError, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
