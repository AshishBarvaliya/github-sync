import frappe
from frappe import _
import requests
import json
import html2text
from bs4 import BeautifulSoup

# def convert_html_to_markdown(html):
#     soup = BeautifulSoup(html, 'html.parser')

#     # Handling checkboxes
#     for li in soup.find_all('li'):
#         if li.get('data-list') == 'unchecked':
#             markdown_checkbox = "- [ ] " + ''.join(map(str, li.contents))
#             li.replace_with(markdown_checkbox)
#         elif li.get('data-list') == 'checked':
#             markdown_checkbox = "- [x] " + ''.join(map(str, li.contents))
#             li.replace_with(markdown_checkbox)

#     # Convert the updated HTML to Markdown
#     converter = html2text.HTML2Text()
#     converter.ignore_links = False
#     converter.ignore_emphasis = False
#     converter.ignore_images = True
#     converter.ignore_anchors = False
#     converter.bypass_tables = False
#     converter.strong_mark = '**'
#     converter.emphasis_mark = '*'
#     markdown = converter.handle(str(soup))
#     return markdown

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

@frappe.whitelist()
def before_insert_task(doc, method, *args, **kwargs):
    if doc.project:
        connection = frappe.get_doc("Github Connection", {"project": doc.project})
        if connection:
            if doc.github_sync_with_github == 1:
                try:
                    last_task = frappe.get_last_doc("Task", {"github_sync_with_github": 1, "project": doc.project})
                    if last_task and last_task.github_sync_issue_index:
                        doc.github_sync_issue_index = last_task.github_sync_issue_index + 1
                    else:
                        doc.github_sync_issue_index = 1

                except frappe.DoesNotExistError:
                        doc.github_sync_issue_index = 1
                doc.subject = f"[{connection.tasks_naming_series}-{doc.github_sync_issue_index}] {doc.subject}"

@frappe.whitelist()
def after_insert_task(doc, method, *args, **kwargs):
    if doc.project:
        connection = frappe.get_doc("Github Connection", {"project": doc.project})
        if connection.github_user:
            if doc.github_sync_with_github == 1:
                url = f"https://api.github.com/repos/{connection.github_user}/{connection.repository}/issues"
                headers = {
                    'Authorization': f'token {connection.github_access_token}',
                    'Accept': 'application/vnd.github+json',
                    "X-GitHub-Api-Version": "2022-11-28"
                }
                data = {
                    'title': doc.subject,
                    'body': doc.description
                    # 'body': convert_html_to_markdown(doc.description)
                }
                response = requests.post(url, headers=headers, data=json.dumps(data))

                if response.status_code == 201:
                    issue_url = response.json().get("url")
                    frappe.db.set_value("Task", doc.name, "github_sync_issue_url", issue_url)
                    frappe.msgprint(_("Issue created successfully!"), title="Success")
                else:
                    frappe.throw(_("Error creating issue: " + response.text), title="Error")

                frappe.db.commit()
