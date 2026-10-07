---
title: "ADR-002 Supporting Sections: Alternatives Considered and Verification"
area: governance
tags:
  - adr
  - governance
  - config-isolation
  - alternatives
  - verification
related:
  - ADR-002-config-isolation.md
  - adr_00_document-guide.md
---
# ADR-002 Supporting Sections: Alternatives Considered and Verification

## Purpose

Companion to `ADR-002-config-isolation.md` (ADR-002: Config Isolation). It holds supporting sections moved out of the ADR to keep the ADR within the documentation size limit. The ADR remains the authority for the decision; the section headings in the ADR link here. This document is not a basis for design decisions.

## Alternatives Considered

### Alternative A: Shared common config file

#### Description

All processes read a shared configuration file and reference only the values they need.

#### Advantages

- Centralized configuration management
- Duplication of the same values can be avoided

#### Disadvantages

- Excessive exposure of Secrets
- Configuration interdependence
- Unclear impact scope of configuration changes
- Bloated configuration files

#### Reason for Rejection

Rejected to prioritize Security and Operability and to prevent the excessive Secret exposure and configuration interdependence caused by a shared configuration file.

#### Reconsideration Conditions

- The operational scale grows and centralized configuration management becomes necessary
- Introducing an external configuration store makes Secret separation possible

### Alternative B: Dynamic config resolution at runtime

#### Description

Search for configuration files dynamically at process startup and automatically read whichever configuration files exist.

#### Advantages

- Flexible configuration management
- Configuration files are easy to add

#### Disadvantages

- Unclear configuration ownership
- Unintended configuration loading
- Unclear impact scope of configuration changes

#### Reason for Rejection

Rejected to prioritize Data Integrity and make configuration ownership clear.

#### Reconsideration Conditions

- Dynamic generation of configuration files becomes necessary
- Configuration management in a cloud environment becomes necessary

### Alternative C: No config isolation enforcement

#### Description

Do not enforce configuration separation between processes; each process reads configuration files freely.

#### Advantages

- Simple structure
- Low complexity

#### Disadvantages

- Excessive exposure of Secrets
- Configuration interdependence
- Unclear impact scope of configuration changes
- Security risk

#### Reason for Rejection

Rejected to prioritize Security and prevent configuration leakage across process boundaries.

#### Reconsideration Conditions

- The trust boundary changes significantly
- The system moves to a single-process configuration

## Verification

### Automated Tests

- **Test**: Each process can read only its permitted configuration files
  - **Verifies**: INV-01
  - **Type**: Integration
  - **Blocking**: Yes
- **Status**: Confirmed — `tests/mcp_servers/test_mcp_server_base.py::TestConfigIsolationValidation::test_falsy_own_config_file_raises_error` verifies Config Isolation fail-closed; `tests/mcp_servers/test_mcp_server_base.py::TestConfigIsolationValidation::test_truthy_own_config_file_calls_restrict_to` verifies ConfigLoader.restrict_to call path
  - **Citation**: `tests/shared/test_production_config_validator.py::TestProductionConfigValidatorUnknownTopLevelKeys`, `tests/mcp_servers/test_config_isolation_fail_closed.py`

- **Test**: Access to non-permitted configuration files is rejected
  - **Verifies**: INV-02
  - **Type**: Regression
  - **Blocking**: Yes
- **Status**: Confirmed — `tests/shared/test_production_config_validator.py::TestProductionConfigValidatorUnknownTopLevelKeys` verifies unknown-key rejection in production config validation
  - **Citation**: `tests/shared/test_production_config_validator.py::TestProductionConfigValidatorSecurityProfileEnum`, `tests/mcp_servers/test_config_isolation_fail_closed.py`

- **Test**: An MCP server can start standalone without agent.toml
  - **Verifies**: INV-03
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: The Agent can start without being given MCP-specific Secrets
  - **Verifies**: INV-04
  - **Type**: Integration
  - **Blocking**: Yes

### Startup Validation

- Whether each process's configuration file exists
- Whether configuration files are valid (parseable TOML, required fields)

### Deployment Validation

- Check the SHA256 checksum of `config/workflows/default.json` before and after deployment (`deploy/deploy.sh`)
- Whether the deployed configuration files match the source

### Runtime Monitoring

- Health Check: confirmation that configuration files loaded successfully
- Metrics: configuration file loading events
- Logs: configuration loading events, error events
- Alert conditions: configuration file loading failure, configuration file syntax error

### Manual Review

- Review of configuration file changes
- Configuration file validation before deployment

Register any Invariant without Verification as an unverified item in an Issue.

## Known Deviations

Not applicable. Known Deviations are recorded in `ADR-002-config-isolation.md`.

## Keywords

- adr
- supporting-sections
