## Communication Language

Always reply to the user in **Simplified Chinese (中文)** by default in this project, regardless of the language used in tool output, file contents, or quoted text. Keep code, filenames, commands, and technical identifiers in their original form (usually English); only the surrounding narration / explanation should be in Chinese.

---

<!-- ARIS-CODEX:BEGIN -->
## ARIS Codex Skill Scope
ARIS Codex packages installed in this project: skills-codex
Managed entries: 80
Manifest: `.aris/installed-skills-codex.txt`
ARIS repo root: `/Users/DongbiaoGao/SourceCode/AI-Research/Auto-claude-code-research-in-sleep`
Project skill path: `.agents/skills/<skill-name>`
For ARIS Codex workflows, prefer the project-local skills under `.agents/skills/`.
When a skill needs ARIS helper scripts, resolve the repo root from the manifest or set it explicitly:
`ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' "/Users/DongbiaoGao/SourceCode/Paper/.aris/installed-skills-codex.txt")`
Do not edit or delete symlinked skills in place; update upstream or rerun:
`bash /Users/DongbiaoGao/SourceCode/AI-Research/Auto-claude-code-research-in-sleep/tools/install_aris_codex.sh "/Users/DongbiaoGao/SourceCode/Paper" --reconcile`
For copied Codex installs, use:
`bash /Users/DongbiaoGao/SourceCode/AI-Research/Auto-claude-code-research-in-sleep/tools/smart_update_codex.sh --project "/Users/DongbiaoGao/SourceCode/Paper"`
<!-- ARIS-CODEX:END -->
