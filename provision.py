"""Provision the approved, pinned local-media manifest.

PROV-1: Explicit --approved is required; validate destinations and HTTPS sources.
PROV-2: Verify all gated access before downloading or installing anything.
PROV-3: Atomic downloads must match size and supplied SHA-256; an existing
divergent destination is never overwritten. Record hashes absent upstream.
PROV-4: Install only absent pinned wheels without dependencies or upgrades.
PROV-5: Assemble Kokoro voices offline using safe tensor loads; preserve an
existing equal archive and refuse to overwrite a divergent archive.
PROV-6: Reject every non-HTTPS redirect before constructing its request; remove
Authorization on host changes so Hugging Face credentials cannot follow a CDN.
PROV-ACCESS: Gated failures identify the actual filename/model page and secure
local authentication; never include source query credentials or token values.
Evidence: tests/test_provision.py; no tests accept a model license or install.
"""

from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    """PROV-6: A redirect cannot downgrade transport or extend token scope."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlparse(newurl).scheme != 'https':
            raise ValueError('Refusing a non-HTTPS download redirect')
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected and urllib.parse.urlparse(newurl).hostname != urllib.parse.urlparse(req.full_url).hostname:
            redirected.remove_header('Authorization')
        return redirected


def open_remote(source, method='GET'):
    """Read HTTPS in the child helper; auth is restricted to huggingface.co."""
    parsed = urllib.parse.urlparse(source)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username:
        raise ValueError('Only credential-free HTTPS source URLs are supported')
    headers = {'User-Agent': 'CodexHarnessProvision/1.0'}
    if parsed.hostname == 'huggingface.co':
        token = os.environ.get('HF_TOKEN')
        if not token:
            try:
                from huggingface_hub import get_token
                token = get_token()
            except ImportError:
                pass
        if token:
            headers['Authorization'] = 'Bearer ' + token
    opener = urllib.request.build_opener(SafeRedirect())
    return opener.open(urllib.request.Request(source, headers=headers, method=method), timeout=60)


def validate_manifest(manifest, manifest_path):
    """PROV-1: Constrain writes to the Comfy root and manifest-local downloads."""
    root = Path(manifest['comfy_root']).resolve()
    downloads = (Path(manifest_path).resolve().parent / 'downloads').resolve()
    for item in manifest['files'] + manifest['python_packages']:
        destination = Path(item['destination']).resolve()
        if not destination.is_relative_to(root) and not destination.is_relative_to(downloads):
            raise ValueError('Manifest destination escapes Comfy root or local downloads')
        source = urllib.parse.urlparse(item['source'])
        if source.scheme != 'https' or not source.hostname or source.username or source.password:
            raise ValueError('Manifest sources must be credential-free HTTPS URLs')
        if type(item['size_bytes']) is not int or item['size_bytes'] < 0:
            raise ValueError('Manifest size must be a nonnegative integer')
    assembly = manifest.get('voice_assembly')
    if assembly and not Path(assembly['destination']).resolve().is_relative_to(root):
        raise ValueError('Voice archive destination escapes Comfy root')


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def verify(path, item, expected):
    actual = digest(path)
    if Path(path).stat().st_size != item['size_bytes'] or (expected and actual != expected):
        raise ValueError('Content size or SHA-256 mismatch: ' + str(path))
    return actual


def commit_new(temporary, destination):
    # Windows rename refuses an existing destination; POSIX needs an exclusive link.
    if os.name == 'nt':
        os.rename(temporary, destination)
    else:
        os.link(temporary, destination)


def download_file(item):
    """PROV-3: Return SHA evidence after a verified atomic download or reuse."""
    destination = Path(item['destination'])
    receipt = destination.with_name(destination.name + '.sha256')
    expected = item.get('sha256')
    if not expected and receipt.is_file():
        expected = receipt.read_text(encoding='ascii').strip()
    if destination.exists():
        if not expected:
            raise ValueError('Cannot reuse existing file without a known SHA-256: ' + str(destination))
        return {'destination':str(destination), 'sha256':verify(destination, item, expected), 'reused':True}
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + '.part-' + uuid.uuid4().hex)
    try:
        with open_remote(item['source']) as response, temporary.open('xb') as stream:
            total = 0
            for block in iter(lambda: response.read(1024 * 1024), b''):
                total += len(block)
                if total > item['size_bytes']:
                    raise ValueError('Download exceeds approved size: ' + destination.name)
                stream.write(block)
        actual = verify(temporary, item, expected)
        commit_new(temporary, destination)
        if not item.get('sha256') and not receipt.exists():
            with receipt.open('x', encoding='ascii') as stream:
                stream.write(actual + '\n')
        return {'destination':str(destination), 'sha256':actual, 'reused':False}
    finally:
        temporary.unlink(missing_ok=True)


def selected(manifest, only):
    if only not in {'all', 'speech'}:
        raise ValueError('only must be all or speech')
    if only == 'all':
        return manifest
    return dict(manifest, files=[x for x in manifest['files'] if x.get('purpose', '').startswith('speech-')])


def provision(manifest_path, approved=False, python=None, only='all'):
    """PROV-1/2/4: Gate first, then verified files, missing wheels and voices."""
    if not approved:
        raise PermissionError('Explicit --approved is required before provisioning')
    manifest_path = Path(manifest_path).resolve()
    manifest = selected(json.loads(manifest_path.read_text(encoding='utf-8')), only)
    validate_manifest(manifest, manifest_path)
    python = python or str(Path(manifest['comfy_root']).parent/'python'/'Scripts'/'python.exe')
    def call(mode, index=0):
        if only == 'all':
            return helper(python, manifest_path, mode, index)
        return helper(python, manifest_path, mode, index, only=only)
    for index, item in enumerate(manifest['files']):
        if item.get('gated'):
            call('gate', index)
    before = call('versions')
    for package in manifest['python_packages']:
        name = package['package'].lower().replace('_', '-')
        if before.get(name) and before[name] != package['version']:
            raise ValueError('Preserving installed package: '+name+'=='+before[name]+'; manifest requests '+package['version'])
    results = [call('fetch', i) for i in range(len(manifest['files'])+len(manifest['python_packages']))]
    if manifest['python_packages']:
        call('install')
    if manifest.get('voice_assembly'):
        call('voices')
    result = {'state':'provisioned', 'only':only, 'files':results, 'versions_before':before,
              'versions_after':call('versions')}
    result_path = manifest_path.parent / ('provision-result-' + only + '.json')
    result_path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


def helper(python, manifest_path, mode, index=0, only='all'):
    """Run credential-bearing and Comfy-runtime operations in a child helper."""
    argv = [str(python), str(Path(__file__).resolve()), str(manifest_path), '--approved',
            '--mode', mode, '--index', str(index), '--only', only]
    result = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8',
                            timeout=1800 if mode == 'fetch' else 120,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    if result.returncode:
        error = result.stderr.strip() or 'Provision helper failed: ' + mode
        if mode == 'gate':
            raise PermissionError(error)
        raise ValueError(error)
    return json.loads(result.stdout)


def assemble_voices(manifest):
    """PROV-5: torch.load(weights_only=True), then np.savez to voices_v1.bin."""
    import numpy as np
    import torch
    assembly = manifest['voice_assembly']
    sources = {Path(x['filename']).stem:Path(x['destination']) for x in manifest['files']
               if x.get('purpose') == 'speech-voice-source'}
    voices = {name:torch.load(sources[name], weights_only=True, map_location='cpu').numpy()
              for name in assembly['source_voices']}
    destination = Path(assembly['destination'])
    if destination.exists():
        with np.load(destination, allow_pickle=False) as previous:
            if set(previous.files) != set(voices) or any(not np.array_equal(previous[name], value) for name,value in voices.items()):
                raise ValueError('Existing Kokoro voice archive differs; preserving it')
        return {'destination':str(destination), 'reused':True}
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + '.part-' + uuid.uuid4().hex)
    try:
        with temporary.open('xb') as stream:
            np.savez(stream, **voices)
        with np.load(temporary, allow_pickle=False) as saved:
            if set(saved.files) != set(voices):
                raise ValueError('Voice archive failed validation')
        commit_new(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return {'destination':str(destination), 'sha256':digest(destination), 'voice_count':len(voices)}


def installed_versions():
    return {d.metadata['Name'].lower().replace('_','-'):d.version for d in importlib.metadata.distributions() if d.metadata['Name']}


def run_helper(manifest, mode, index):
    if mode == 'gate':
        try:
            with open_remote(manifest['files'][index]['source'], method='HEAD') as response:
                if response.status != 200:
                    raise PermissionError
        except (urllib.error.URLError, PermissionError):
            item=manifest['files'][index]
            source=urllib.parse.urlsplit(item['source'])
            parts=source.path.strip('/').split('/')
            page='https://'+source.hostname+'/'+'/'.join(parts[:2])
            filename=item.get('filename') or parts[-1]
            raise PermissionError(f'Access denied for {filename}. Accept required model terms at {page} and authenticate the same account using HF_TOKEN or hf auth login in the Comfy Python environment.') from None
        return {'authorized':True}
    if mode == 'versions':
        return installed_versions()
    if mode == 'fetch':
        return download_file((manifest['files']+manifest['python_packages'])[index])
    if mode == 'voices':
        return assemble_voices(manifest)
    if mode == 'install':
        before = installed_versions()
        absent = []
        for package in manifest['python_packages']:
            name = package['package'].lower().replace('_','-')
            if before.get(name) not in {None,package['version']}:
                raise ValueError('Refusing to upgrade or downgrade existing package: '+name)
            if name not in before:
                verify(package['destination'], package, package['sha256'])
                absent.append(package['destination'])
        if absent:
            command = [sys.executable,'-m','pip','install','--no-index','--no-deps','--disable-pip-version-check',*absent]
            result = subprocess.run(command, capture_output=True, text=True, timeout=120)
            if result.returncode:
                raise ValueError('Pinned wheel installation failed: '+result.stderr.strip())
        after = installed_versions()
        if any(after.get(name) != version for name,version in before.items()):
            raise ValueError('Existing package versions changed unexpectedly')
        return {'installed':[x['package'] for x in manifest['python_packages'] if x['package'].lower().replace('_','-') not in before]}
    raise ValueError('Unknown helper mode')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--approved', action='store_true')
    parser.add_argument('--python')
    parser.add_argument('--only', choices=['all','speech'], default='all')
    parser.add_argument('--mode', choices=['provision','gate','fetch','versions','install','voices'], default='provision', help=argparse.SUPPRESS)
    parser.add_argument('--index', type=int, default=0, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if not args.approved:
            raise PermissionError('Explicit --approved is required before provisioning')
        if args.mode == 'provision':
            result = provision(args.manifest, args.approved, args.python, args.only)
        else:
            manifest = selected(json.loads(args.manifest.read_text(encoding='utf-8')), args.only)
            validate_manifest(manifest, args.manifest)
            result = run_helper(manifest, args.mode, args.index)
        print(json.dumps(result))
        return 0
    except (ValueError,PermissionError,OSError,subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
