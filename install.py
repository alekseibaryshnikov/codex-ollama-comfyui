"""Install or roll back the global Codex integration.

INSTALL-1: Refuse activation until all requested smoke capabilities pass; back up
every touched file, preserve unrelated settings/instructions, and refuse rollback
over subsequent user edits. Evidence: tests/test_install.py. Fixture tests prove
filesystem/config behavior, not whether Codex discovers roles after restart.
INSTALL-2: Activation requires verified image_edit and video_edit presets.
INSTALL-LTX: New installs name LTX-2.5 generation and experimental regeneration.
Evidence: tests/test_install.py.
INSTALL-CODER-EVIDENCE: Fresh activation requires separate native coder evidence;
refresh of an activated profile does not invent or re-run media evidence.
Evidence: tests/test_install.py.
INSTALL-REFRESH: Refresh only an already activated Sol/OpenAI profile; preserve
root and surrounding bytes, refuse ambiguous skills, and allow rollback. Evidence:
tests/test_native_migration.py.
INSTALL-NATIVE: Stage, activate and roll back distinct native coding and review roles;
route bounded coding to terra_coder and independent fresh review to terra.
Evidence: tests/test_install.py and tests/test_portability.py.
INSTALL-PORTABLE: Render the actual checkout and selected profile paths. Stage
roles and the user skill under the profile's .agents/skills without modifying
root settings/routing; activation retains smoke evidence gates and rollback.
Evidence: tests/test_portability.py.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import tomllib
import uuid

BASE = Path(__file__).resolve().parent

def skill_path(codex_home):
    home = Path(codex_home).resolve()
    canonical = home.parent/'.agents/skills/local-harness/SKILL.md'
    legacy = home/'skills/local-harness/SKILL.md'
    if canonical.exists() and legacy.exists():
        raise ValueError('Both canonical and legacy local-harness skills exist')
    return legacy if legacy.exists() else canonical


def _agent_payloads(home):
    payloads={}
    for name in ['astra','terra','terra_coder']:
        data=(BASE/'integration'/f'{name}.toml').read_bytes()
        tomllib.loads(data.decode('utf-8'))
        payloads[home/'agents'/f'{name}.toml']=data
    skill=(BASE/'integration/SKILL.md').read_text(encoding='utf-8')
    payloads[skill_path(home)]=skill.replace('__HARNESS_ROOT__',BASE.resolve().as_posix()).encode('utf-8')
    return payloads


def stage(codex_home):
    home=Path(codex_home).resolve()
    return _apply(home,_agent_payloads(home),{'stage_only':True})
REQUIRED = {'tests','terra_coder','terra','astra','image','image_edit','video','video_edit','music','speech','sfx'}
MARKER = '''<!-- local-harness:start -->
For local coding and asset-generation tasks, load and follow the local-harness
skill at __SKILL_PATH__. Sol coordinates and delegates routine bounded coding
to native terra_coder. A separate fresh native terra session independently reviews
every implementation and repair. Native astra handles difficult decisions and
unresolved failures. No Qwen or Ollama automatic coding route or fallback is used.
Use registered ComfyUI presets for assets, with LTX-2.5 for video generation.
The LTX video_edit route is experimental source-guided regeneration.
This explicitly requests those subagents when the workflow calls for them.
Worker and specialist sessions perform their bounded assignment without
recursively invoking the coordinator workflow. Other user/project instructions
and authorization boundaries still apply.
<!-- local-harness:end -->
'''


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _atomic(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    temporary.write_bytes(data)
    os.replace(temporary,path)


def activate(codex_home, evidence):
    missing=sorted(key for key in REQUIRED if evidence.get(key) is not True)
    if missing:
        raise ValueError('Unverified capabilities: '+', '.join(missing))
    home=Path(codex_home).resolve()
    config_path=home/'config.toml'
    old_config=config_path.read_text(encoding='utf-8-sig') if config_path.exists() else ''
    tomllib.loads(old_config)
    lines=old_config.splitlines(keepends=True)
    retained=[]
    top=True
    for line in lines:
        if line.lstrip().startswith('['):top=False
        if top and re.match(r'^\s*(model|model_provider|model_reasoning_effort|openai_base_url|model_catalog_json)\s*=',line):
            continue
        retained.append(line)
    config='model = "gpt-6.1-sol"\nmodel_provider = "openai"\nmodel_reasoning_effort = "high"\n'+''.join(retained)
    tomllib.loads(config)
    agent_path=home/'AGENTS.md'
    instructions=agent_path.read_text(encoding='utf-8-sig') if agent_path.exists() else ''
    instructions=re.sub(r'(?s)\n?<!-- local-harness:start -->.*?<!-- local-harness:end -->\n?','',instructions)
    marker=MARKER.replace('__SKILL_PATH__',skill_path(home).as_posix())
    payloads={config_path:config.encode(),agent_path:(instructions.rstrip()+'\n\n'+marker).encode()}
    payloads.update(_agent_payloads(home))
    return _apply(home,payloads,evidence)


def refresh(codex_home):
    home = Path(codex_home).resolve()
    skill = skill_path(home)
    config = tomllib.loads((home/'config.toml').read_text(encoding='utf-8-sig'))
    if config.get('model') != 'gpt-6.1-sol' or config.get('model_provider') != 'openai':
        raise ValueError('Refresh requires activated Sol/OpenAI root configuration')
    target = home/'AGENTS.md'
    raw = target.read_bytes()
    start, end = b'<!-- local-harness:start -->', b'<!-- local-harness:end -->'
    if raw.count(start) != 1 or raw.count(end) != 1 or raw.index(start) > raw.index(end):
        raise ValueError('Refresh requires exactly one local-harness block')
    left = raw.index(start); right = raw.index(end) + len(end)
    marker = MARKER.replace('__SKILL_PATH__',skill.as_posix()).rstrip('\n').encode('utf-8')
    payloads = {target:raw[:left]+marker+raw[right:]}
    payloads.update(_agent_payloads(home))
    return _apply(home,payloads,{'refresh_only':True})


def _apply(home,payloads,evidence):
    for target in payloads:
        allowed=home.parent if target==skill_path(home) else home
        if not target.resolve().is_relative_to(allowed) or target.is_symlink():
            raise ValueError(f'Integration target escapes Codex home: {target}')
    backup=home/'harness-backups'/str(uuid.uuid4())
    backup.mkdir(parents=True)
    files=[]
    for index,(target,data) in enumerate(payloads.items()):
        original=target.read_bytes() if target.exists() else None
        record={'target':str(target),'original':str(index) if original is not None else None,'installed_sha256':_hash(data)}
        if original is not None:(backup/str(index)).write_bytes(original)
        files.append(record)
    (backup/'manifest.json').write_text(json.dumps({'files':files,'evidence':evidence},indent=2),encoding='utf-8')
    completed=[]
    try:
        for target,data in payloads.items():
            _atomic(target,data)
            completed.append(target)
    except Exception:
        for record in files:
            target=Path(record['target'])
            if target in completed:
                if record['original'] is None:target.unlink()
                else:_atomic(target,(backup/record['original']).read_bytes())
        raise
    return backup


def rollback(backup):
    backup=Path(backup)
    manifest=json.loads((backup/'manifest.json').read_text(encoding='utf-8'))
    for item in manifest['files']:
        target=Path(item['target'])
        if not target.is_file() or _hash(target.read_bytes()) != item['installed_sha256']:
            raise ValueError(f'Refusing rollback over subsequent changes: {target}')
    for item in manifest['files']:
        target=Path(item['target'])
        if item['original'] is None:target.unlink()
        else:_atomic(target,(backup/item['original']).read_bytes())


def main():
    parser=argparse.ArgumentParser(description='Activate verified Codex routing or restore a backup')
    actions=parser.add_subparsers(dest='action',required=True)
    staged=actions.add_parser('stage',help='Install roles and skill without changing root routing')
    staged.add_argument('--codex-home',type=Path,default=Path(os.environ.get('CODEX_HOME',Path.home()/'.codex')))
    refreshed=actions.add_parser('refresh',help='Refresh an already activated profile without changing root settings')
    refreshed.add_argument('--codex-home',type=Path,default=Path(os.environ.get('CODEX_HOME',Path.home()/'.codex')))
    active=actions.add_parser('activate')
    active.add_argument('--codex-home',type=Path,default=Path(os.environ.get('CODEX_HOME',Path.home()/'.codex')))
    active.add_argument('--evidence',type=Path,required=True)
    undo=actions.add_parser('rollback');undo.add_argument('backup',type=Path)
    args=parser.parse_args()
    if args.action=='stage':
        print(json.dumps({'backup':str(stage(args.codex_home)),'routing_enabled':False}))
    elif args.action=='refresh':
        print(json.dumps({'backup':str(refresh(args.codex_home))}))
    elif args.action=='activate':
        evidence=json.loads(args.evidence.read_text(encoding='utf-8'))
        print(json.dumps({'backup':str(activate(args.codex_home,evidence))}))
    else:
        rollback(args.backup)
        print(json.dumps({'restored':str(args.backup)}))


if __name__=='__main__':main()
