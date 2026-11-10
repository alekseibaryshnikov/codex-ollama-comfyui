# Standalone skills inventory

The recovery catalog covers 131 skills across 1,672 files. Its entries record the installed relative paths, SHA-256 digests, sizes and text normalization rule. Each of the 1,653 upstream files matched a Git blob at the revision linked below. This includes the Video Shotcraft templates, gallery, workbench and media. The catalog retains the full installed trees, including supporting scripts, references and icons. See the [file manifest](../manifests/skills.json).

| Pinned source | Skills | Repository license |
| --- | ---: | --- |
| [upstash/context7](https://github.com/upstash/context7/tree/eb579860bf7c31427690fdac2d2e1949507e9296) | 1 | [MIT](https://github.com/upstash/context7/blob/eb579860bf7c31427690fdac2d2e1949507e9296/LICENSE) |
| [emilkowalski/skills](https://github.com/emilkowalski/skills/tree/2d228630ba1446365f614a108cb8252f1feda202) | 15 | [MIT](https://github.com/emilkowalski/skills/blob/2d228630ba1446365f614a108cb8252f1feda202/LICENSE) |
| [gamedev-skills/awesome-gamedev-agent-skills](https://github.com/gamedev-skills/awesome-gamedev-agent-skills/tree/19d93f97c9c1ea0f8b306e77aa81e0d3e352d3e9) | 78 | [Apache-2.0](https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/19d93f97c9c1ea0f8b306e77aa81e0d3e352d3e9/LICENSE) |
| [blader/humanizer](https://github.com/blader/humanizer/tree/8c307f367c91bd974002f10f2be2965d642c13df) | 1 | [MIT](https://github.com/blader/humanizer/blob/8c307f367c91bd974002f10f2be2965d642c13df/LICENSE) |
| [phaserjs/phaser](https://github.com/phaserjs/phaser/tree/02d8931b626d9764c133cbb3fbf99966c03c757c) | 28 | [MIT](https://github.com/phaserjs/phaser/blob/02d8931b626d9764c133cbb3fbf99966c03c757c/LICENSE.md) |
| [typesafe-ai/skills](https://github.com/typesafe-ai/skills/tree/65a39f393687675ce170e6094757de20370365b9) | 1 | [MIT](https://github.com/typesafe-ai/skills/blob/65a39f393687675ce170e6094757de20370365b9/LICENSE) |
| [vercel-labs/skills](https://github.com/vercel-labs/skills/tree/7407f3893ad4dceab546ac002c3ef806e4000c73) | 1 | [MIT](https://github.com/vercel-labs/skills/blob/7407f3893ad4dceab546ac002c3ef806e4000c73/LICENSE) |
| [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft/tree/43bd349a136651865ecfa6ea1cf012f6e957d304) | 1 | [Apache-2.0](https://github.com/Vincentwei1021/video-shotcraft/blob/43bd349a136651865ecfa6ea1cf012f6e957d304/LICENSE) |

Five local skills account for the other 19 files. The snapshots include `ai-cinematic-short-film`, `design-web-apps`, `game-reward-design`, `sdd-tdd` and `stake-submission-review`. The Stake reference preserves 51 checkbox labels supplied by the user on 9 November 2026. The original UI revision, capture date and account scope are unknown. See the [local snapshots](../skills/local/) and [checklist provenance](../skills/local/stake-submission-review/references/checklist.md).

The original inventory contained 125 standalone skills in `~/.agents/skills` and 22 in `~/.codex/skills`. The 15 duplicate names had identical file contents after normalizing CRLF to LF. The harness installer renders the remaining `local-harness` skill separately with the destination's actual paths. Codex manages its system skills, and plugins use their own installer.

The original `~/.agents/.skill-lock.json` recorded source repository and skill paths for 96 installed names. Four older Stake entries had no corresponding installed folder and were excluded. Phaser, Context7 and Video Shotcraft were verified directly against pinned repository trees. Some lock hashes refer to directory trees, so the catalog pins a full repository commit and checks each installed file independently.

Restoring files does not exercise individual skill workflows. Some skills need additional tools or services. For example, Context7 uses a configured MCP server, and Video Shotcraft's Node-based tools have their own dependency manifests.
