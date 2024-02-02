import frappe
import json
from frappe import _
from github_sync.utils import verify_signature
from github_sync.utils.github import handle_issue_comment_webhook, handle_issue_webhook
import requests

@frappe.whitelist(methods=["GET"], allow_guest=True)
def callback(code):
    response = requests.post("https://github.com/login/oauth/access_token", data={
        "client_id": frappe.conf.github_client_id,
        "client_secret": frappe.conf.github_client_secret,
        "code": code
    }, headers={"Accept": "application/json"})
    if not response.ok:
        return "Github Access Token Not Found! ⚠️"
    payload = response.json()
    access_token = (payload.get("access_token") or "")
    frappe.local.cookie_manager.set_cookie("github_access_token", access_token)
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = frappe.utils.get_url() + "/app/github-connection/new-github-connection"

@frappe.whitelist(methods=["POST"])
def get_config(key):
    return frappe.conf[key]

@frappe.whitelist()
def github_logout():
    frappe.local.cookie_manager.delete_cookie("github_access_token")
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = frappe.utils.get_url() +"/app/github-connection/new-github-connection"

@frappe.whitelist(methods=["POST"], allow_guest=True)
def webhook():
    raw_data = frappe.request.get_data()
    data = json.loads(raw_data)
    
    repo = data.get("repository", {}).get("name", "")
    user = data.get("repository", {}).get("owner", {}).get("login", "")
    x_hub_signature = frappe.request.headers.get('X-Hub-Signature')
    
    connection = frappe.db.get_value("Github Connection", {"repository": repo, "github_user": user}, ["github_webhook_secret", "project", "tasks_naming_series", "repository", "github_user"], as_dict=1)

    if not connection:
        frappe.log_error("Github Webhook Secret Not Found", "Webhook Error")
        return "Github Webhook Secret Not Found", 403
    
    if not verify_signature(raw_data, x_hub_signature, secret=connection.github_webhook_secret):
        frappe.log_error("Signature verification failed", "Webhook Error")
        return "Invalid signature", 403

    event = frappe.request.headers.get("X-GitHub-Event")

    if event == "issue_comment":
        handle_issue_comment_webhook(data, connection)
    elif event == "issues":
        handle_issue_webhook(data, connection)
    return "Webhook processed successfully"
