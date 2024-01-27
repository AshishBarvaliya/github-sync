import frappe
from frappe import _
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
    frappe.local.response["location"] = "http://localhost:8000/app/github-connection/new-github-connection"

@frappe.whitelist(methods=["POST"])
def get_config(key):
    return frappe.conf[key]

@frappe.whitelist()
def github_logout():
    frappe.local.cookie_manager.delete_cookie("github_access_token")
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = "http://localhost:8000/app/github-connection/new-github-connection"
