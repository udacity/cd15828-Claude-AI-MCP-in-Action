# Claude AI: MCP in Action

This repo holds a set of hands-on exercises grouped into two projects, each a self-contained
Python codebase that you build up one exercise at a time.

## Folder Structure

Each project folder contains a sequence of numbered exercise folders, and each exercise folder
provides a `starter/` (scaffold with `# TODO` blocks to implement) and a `solution/` (complete
reference implementation):

```bash
<Project Name>/
└── NN-exercise-name/
    ├── starter/      # scaffold with TODOs — the implementation starting point
    │   └── README.md # exercise instructions
    └── solution/     # complete reference implementation
        └── README.md
```

Each `starter/` and `solution/` is an installable Python package with its own `pyproject.toml`
and `pytest` suite. The exercises within a project are cumulative: each one assumes the previous
exercise's work is already in place, and the final exercise brings the project to the full
reference solution.

## Projects

### Build an Inventory Agent with MCP Tools

Build an MCP-backed inventory agent, focusing on how tools are defined, described, and selected.

1. **`01-structured-tool-results`** — Return a uniform `ToolResult` error envelope from every
   tool, with categories an agent can act on (retry, stop, escalate).
2. **`02-differentiated-tool-descriptions`** — Write differentiated, single-purpose tool
   descriptions with explicit boundary clauses so the agent routes intents correctly.
3. **`03-tool-distribution-and-choice`** — Control which tool schemas the model sees and set the
   `tool_choice` policy (forced / `any` / `auto`), with a guard enforcing call ordering.
4. **`04-built-in-vs-custom-selection`** — Build a priority-ordered rule table that selects the
   narrowest correct tool (built-in vs. custom) for a given task.

### Implement MCP Governance with Scoped Config and an Audited Agent Loop

Build a governed MCP setup with scoped configuration, a secret-leak CI gate, and an audited
agent loop.

1. **`01-scoped-config-ci-gate`** — Load and tag project vs. personal MCP config scopes, expand
   `${VAR}` references, and gate against leaked literal secrets in CI.
2. **`02-governed-tools`** — Define custom servers with governed tool descriptions, a decision
   rule table, and a `claims://schema` MCP resource.
3. **`03-audited-loop`** — Build an audited agent loop with an append-only audit trail and a
   tool-runner gateway that records one entry per call.

## Running an Exercise

Each exercise's `README.md` has the exact steps. The common pattern, run from inside a `starter/`
or `solution/` folder:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
```

Work through the `# TODO` blocks named in the exercise README, then run the verifying test file
until it is green.
