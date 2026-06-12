# Goal

Add a `McpInstallParams` DTO to `mcp_install.py` that groups the interactive
install parameters (`port`, `role`, `with_confd`) gathered by `InstallQA`, and
make `McpInstallService.run()` accept it instead of querying `InstallQA` directly
for individual fields.

# Scope

- `scripts/agent/services/mcp_install.py`

# Assumptions

1. `McpInstallService.run(server_name, qa)` currently queries `qa.ask_port()`,
   `qa.ask_role()`, `qa.ask_confd()` inline. After this change, a separate step
   collects all parameters via `InstallQA` into `McpInstallParams`, and `run()`
   accepts the DTO.
2. The DTO is named `McpInstallParams` (not `McpInstallRequest`) to distinguish it
   from the command-layer `McpInstallRequest` in `agent/commands/models.py` which
   only holds `server_name`.
3. `CliInstallQA` remains unchanged as the I/O layer; only `McpInstallService.run()`
   signature changes.
4. `ScaffoldResult` is already a dataclass; no change needed.
5. `_VALID_ROLES` validation stays in the service; `McpInstallParams` holds already-
   validated values.
6. The call site in `cmd_mcp._cmd_mcp_install()` is updated to call a new helper
   `await svc.collect_params(server_name, qa)` before `run()`.

# Implementation

## Target file

`scripts/agent/services/mcp_install.py`
`scripts/agent/commands/cmd_mcp.py` (call site update)

## Procedure

1. Add `McpInstallParams` frozen dataclass:
   ```python
   @dataclass(frozen=True)
   class McpInstallParams:
       server_name: str
       port: int
       role: str
       with_confd: bool
   ```

2. Add `McpInstallService.collect_params(server_name, qa)` async method:
   ```python
   async def collect_params(
       self, server_name: str, qa: InstallQA
   ) -> McpInstallParams:
       port = await qa.ask_port(default=8000)
       role = await qa.ask_role()
       if role not in _VALID_ROLES:
           raise ValueError(
               f"Invalid role {role!r}. Valid: {', '.join(sorted(_VALID_ROLES))}"
           )
       with_confd = await qa.ask_confd()
       return McpInstallParams(
           server_name=server_name,
           port=port,
           role=role,
           with_confd=with_confd,
       )
   ```

3. Refactor `McpInstallService.run()` to accept `McpInstallParams`:
   ```python
   async def run(self, params: McpInstallParams) -> ScaffoldResult:
       # Use params.server_name, params.port, params.role, params.with_confd
       # instead of querying qa inline
   ```

4. Update `cmd_mcp._cmd_mcp_install()` call site:
   ```python
   svc = McpInstallService()
   qa = CliInstallQA()
   params = await svc.collect_params(server_name, qa)
   result = await svc.run(params)
   ```

5. Run ruff + mypy.

## Method

Extract parameter collection into a DTO builder (`collect_params`). `run()` becomes
a pure function of `McpInstallParams` — no I/O, fully testable without a real terminal.

# Validation plan

- `uv run ruff check scripts/agent/services/mcp_install.py scripts/agent/commands/cmd_mcp.py`
- `uv run mypy scripts/agent/services/mcp_install.py scripts/agent/commands/cmd_mcp.py`
- `uv run pytest tests/ -k "mcp_install or cmd_mcp" --ignore=tests/test_create_schema.py -v`
