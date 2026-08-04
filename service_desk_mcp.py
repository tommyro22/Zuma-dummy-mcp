from mcp.server import MCPServer as FastMCP
from pydantic import Field
import uuid
import os

mcp = FastMCP("IT-Service-Desk-MCP")

TICKETS = {
    "TICK-101": {"user_id": "usr_882", "issue": "VPN Access Issue", "status": "Open"},
    "TICK-102": {"user_id": "usr_104", "issue": "CRM Permission Denied", "status": "Resolved"}
}

@mcp.tool()
def get_ticket_status(ticket_id: str = Field(description="Ticket ID (e.g., TICK-101)")) -> dict:
    """Retrieve IT support ticket status."""
    return {"found": True, "ticket": TICKETS[ticket_id]} if ticket_id in TICKETS else {"found": False}

@mcp.tool()
def create_support_ticket(user_id: str, issue_description: str) -> dict:
    """Create a new IT support ticket."""
    new_id = f"TICK-{uuid.uuid4().hex[:4].upper()}"
    TICKETS[new_id] = {"user_id": user_id, "issue": issue_description, "status": "Open"}
    return {"success": True, "ticket_id": new_id, "status": "Open"}

@mcp.tool()
def force_password_reset(user_id: str, reason: str) -> dict:
    """HIGH RISK: Revoke tokens and force password reset."""
    return {"success": True, "action": "FORCE_RESET", "user_id": user_id}

@mcp.tool()
def purge_audit_logs(retention_days: int = 0) -> dict:
    """DESTRUCTIVE: Permanently delete audit logs."""
    return {"success": True, "purged_records": 4820}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # Switch from "sse" to "streamable-http"
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
