# Implementation: docs/ — Update documentation references from agent/config.py to direct modules

**Plan source:** `plans/20260702-202905_plan.md` (Phase 5 (steps 13-15))
**Target file:** `docs/`

---

## Goal

docs/ 配下の 3 つのドキュメントファイルで `agent/config.py` への参照を `agent/config_builders.py` または `agent/config_dataclasses.py` に更新し、削除されたファイルへの言及を除去する。

---

## Scope

**In:**
- `docs/05_agent_08_configuration.md`: "agent/config.py:627" を "agent/config_builders.py" に更新 (正確な行番号も合わせて修正)
- `docs/05_agent_01_system-overview.md`: テーブルセル内 "agent/config.py" を "agent/config_dataclasses.py" に更新
- `docs/05_agent_13_reference-api.md`: セクション見出し "## AgentConfig (agent/config.py)" を "## AgentConfig (agent/config_dataclasses.py)" に更新

**Out:**
- ドキュメントの内容・説明文の変更
- 上記 3 ファイル以外のドキュメント変更

---

## Assumptions

1. `build_agent_config` のような builder 関数は `agent/config_builders.py` に定義されているため、`05_agent_08_configuration.md` の参照先は `config_builders.py` が正しい
2. `AgentConfig` はデータクラスであるため `agent/config_dataclasses.py` に定義されている
3. 行番号は `scripts/agent/config_builders.py` の実際の行数を確認してから更新する

---

## Implementation

### Target file

`docs/`

### Procedure

1. `docs/05_agent_08_configuration.md` を開き、"agent/config.py:627" の参照を特定する。`scripts/agent/config_builders.py` の該当シンボルの実際の行番号を確認してから "agent/config_builders.py:<line>" に更新する。
2. `docs/05_agent_01_system-overview.md` を開き、テーブル内の "agent/config.py" セルを "agent/config_dataclasses.py" に更新する。
3. `docs/05_agent_13_reference-api.md` を開き、見出し "## AgentConfig (agent/config.py)" を "## AgentConfig (agent/config_dataclasses.py)" に更新する。

### Method

Edit tool でドキュメント編集

### Details

各ファイルの変更パターン:

**05_agent_08_configuration.md:**
```markdown
# Before
agent/config.py:627

# After
agent/config_builders.py:<actual_line_number>
```

**05_agent_01_system-overview.md (テーブルセル):**
```markdown
# Before
| ... | agent/config.py | ... |

# After
| ... | agent/config_dataclasses.py | ... |
```

**05_agent_13_reference-api.md (セクション見出し):**
```markdown
# Before
## AgentConfig (agent/config.py)

# After
## AgentConfig (agent/config_dataclasses.py)
```

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 残存参照確認 | grep -R "agent/config.py" docs/ | 変更対象以外の参照がないこと |
| Lint (docs) | N/A (Markdown) | 目視確認 |
| Tests | uv run pytest | all pass |
