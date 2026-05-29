[prerequisites]
- routing
- dependency direction
- minimal loading
- shared normalization

[tasks]
CLAUDE.md, skills/DESIGN.md, `skills/**/*.md` の内容の重複を削除
Context Loader Pattern を考慮し、CCLAUDE.md, skills/DESIGN.md, `skills/**/*.md` を再構成
```
Task
 ↓
Routing
 ↓
Minimal Skills
 ↓
Shared Rules
 ↓
Execution
```
