"""MCP governance toolkit for the Northwind Mutual claims platform.

The package operationalizes the four enterprise MCP decisions:

* **registry** -- :class:`~mcp_governance.scoping.McpConfig`, the scoped ``.mcp.json`` /
  ``~/.claude.json`` server catalog;
* **identity** -- the project-vs-personal ``scope`` carried onto every audit entry;
* **gateway** -- :class:`~mcp_governance.audit.AuditedToolRunner` (and the ``ci-check`` gate);
* **audit trail** -- the append-only :class:`~mcp_governance.audit.AuditTrail`.
"""

__version__ = "0.2.0"
