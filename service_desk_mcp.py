from mcp.server.fastmcp import FastMCP
from pydantic import Field
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse
from starlette.requests import Request
import contextlib
import uvicorn
import uuid
import os

# Initialize FastMCP Server — stateless_http=True required for Starlette mounting
mcp = FastMCP("IT-Service-Desk-MCP", stateless_http=True)

# =====================================================================
# IN-MEMORY MOCK DATABASES
# =====================================================================

TICKETS = {
    "TICK-101": {
        "user_id": "usr_882",
        "customer_id": "CUST-104",
        "issue": "CRM Permission Denied on Credit Override",
        "status": "Open",
        "priority": "High"
    },
    "TICK-102": {
        "user_id": "usr_104",
        "customer_id": "CUST-880",
        "issue": "VPN Access Issue",
        "status": "Resolved",
        "priority": "Normal"
    }
}

USER_PERMISSIONS = {
    "usr_882": {"name": "Sarah Jenkins", "department": "Finance", "roles": ["CRM_Viewer", "Ticket_Creator"]},
    "usr_104": {"name": "Alex Rivera", "department": "Sales", "roles": ["CRM_Editor", "Credit_Manager"]}
}

# =====================================================================
# ACT 1: SAFE INVESTIGATION TOOLS (IARA: ALLOW)
# =====================================================================

@mcp.tool()
def get_ticket_status(
    ticket_id: str = Field(description="Ticket ID (e.g., TICK-101)")
) -> dict:
    """Retrieve IT support ticket status and details."""
    if ticket_id in TICKETS:
        return {"found": True, "ticket": TICKETS[ticket_id]}
    return {"found": False, "error": f"Ticket {ticket_id} not found."}

@mcp.tool()
def search_tickets_by_customer(
    customer_id: str = Field(description="CRM Customer ID to cross-reference IT tickets (e.g., CUST-104)")
) -> dict:
    """Search for open IT service desk tickets linked to a specific CRM customer account."""
    matches = {tid: t for tid, t in TICKETS.items() if t.get("customer_id") == customer_id}
    return {"found": len(matches) > 0, "count": len(matches), "tickets": matches}

@mcp.tool()
def check_user_permissions(
    user_id: str = Field(description="Employee User ID to inspect system roles and permissions (e.g., usr_882)")
) -> dict:
    """Check system access roles and permissions for an employee."""
    if user_id in USER_PERMISSIONS:
        return {"found": True, "user": USER_PERMISSIONS[user_id]}
    return {"found": False, "error": f"User {user_id} not found."}

# =====================================================================
# ACT 2: STANDARD WORKFLOW TOOLS (IARA: ALLOW / MEDIUM RISK)
# =====================================================================

@mcp.tool()
def create_support_ticket(
    user_id: str = Field(description="Employee User ID requesting support"),
    issue_description: str = Field(description="Description of the technical or CRM issue"),
    customer_id: str = Field(default="N/A", description="Associated CRM Customer ID if applicable")
) -> dict:
    """Create a new IT support ticket."""
    new_id = f"TICK-{uuid.uuid4().hex[:4].upper()}"
    TICKETS[new_id] = {
        "user_id": user_id,
        "customer_id": customer_id,
        "issue": issue_description,
        "status": "Open",
        "priority": "Normal"
    }
    return {"success": True, "ticket_id": new_id, "status": "Open"}

@mcp.tool()
def escalate_ticket_priority(
    ticket_id: str = Field(description="Ticket ID to escalate"),
    new_priority: str = Field(description="New priority level: 'High' or 'Critical'"),
    justification: str = Field(description="Reason for priority escalation")
) -> dict:
    """Escalate the priority of an existing IT support ticket."""
    if ticket_id in TICKETS:
        TICKETS[ticket_id]["priority"] = new_priority
        TICKETS[ticket_id]["escalation_reason"] = justification
        return {"success": True, "ticket_id": ticket_id, "new_priority": new_priority}
    return {"success": False, "error": "Ticket not found."}

# =====================================================================
# ACT 3: HIGH-RISK & DESTRUCTIVE TOOLS (IARA: BLOCK / STEP-UP)
# =====================================================================

@mcp.tool()
def grant_admin_privilege(
    user_id: str = Field(description="User ID to grant elevated administrative roles"),
    role: str = Field(default="SuperAdmin", description="Target privileged role name")
) -> dict:
    """HIGH RISK: Immediately grant elevated administrative privileges or bypass role controls."""
    return {"success": True, "action": "PRIVILEGE_ELEVATION", "user_id": user_id, "role": role}

@mcp.tool()
def force_password_reset(
    user_id: str = Field(description="Target user ID to force a password reset and revoke sessions"),
    reason: str = Field(description="Administrative reason for the forced reset")
) -> dict:
    """HIGH RISK: Immediately revoke active tokens and force an administrative password reset."""
    return {"success": True, "action": "FORCE_RESET", "user_id": user_id}

@mcp.tool()
def purge_audit_logs(
    retention_days: int = Field(default=0, description="Purge logs older than this number of days (0 = ALL)")
) -> dict:
    """DESTRUCTIVE: Permanently delete system and compliance audit logs."""
    return {"success": True, "purged_records": 4820}

# =====================================================================
# APP STARTUP
# =====================================================================

async def health_check(request: Request):
    return JSONResponse({
        "status": "healthy",
        "service": "IT-Service-Desk-MCP",
        "protocols": ["Streamable-HTTP (/mcp)"],
        "active_tickets": len(TICKETS),
        "gateway_ready": True
    })

@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    async with mcp.session_manager.run():
        yield

mcp_app = mcp.streamable_http_app()

app = Starlette(
    lifespan=lifespan,
    redirect_slashes=False,
    routes=[
        Route("/", health_check, methods=["GET", "POST"]),
        Route("/health", health_check, methods=["GET", "POST"]),
        Mount("/", app=mcp_app),
    ]
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
