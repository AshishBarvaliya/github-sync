import frappe
import requests
import json
from frappe import _
import html2text
from bs4 import BeautifulSoup

github_user="githubuser@example.com"
admin="Administrator"

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

def create_github_issue(doc, connection):
    url = f"https://api.github.com/repos/{connection.github_user}/{connection.repository}/issues"
    headers = {
        'Authorization': f'token {connection.github_access_token}',
        'Accept': 'application/vnd.github+json',
        "X-GitHub-Api-Version": "2022-11-28"
    }
    data = {
        'title': doc.subject,
        'body': doc.description if doc.description else "",
        # 'body': convert_html_to_markdown(doc.description)
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 201:
        issue_number = response.json().get("number")
        doc.github_sync_github_user = connection.github_user
        doc.github_sync_github_repo = connection.repository
        doc.github_sync_github_issue_number = issue_number
        doc.save(ignore_permissions=True)
    else:
        frappe.throw(_("Error creating issue: " + response.text), title="Error")

def update_github_issue(doc, connection):
    url = f"https://api.github.com/repos/{doc.github_sync_github_user}/{doc.github_sync_github_repo}/issues/{doc.github_sync_github_issue_number}"

    headers = {
        'Authorization': f'token {connection.github_access_token}',
        'Accept': 'application/vnd.github+json',
        "X-GitHub-Api-Version": "2022-11-28"
    }
    data = {
        'title': doc.subject,
        'body': doc.description if doc.description else "",
        # 'body': convert_html_to_markdown(doc.description)
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if not response.ok:
        frappe.throw(_("Error updating issue: " + response.text), title="Error")

def delete_github_webhook(webhook_id, repo, user, access_token):
    url = f"https://api.github.com/repos/{user}/{repo}/hooks/{webhook_id}"
    headers = {
        'Authorization': f'token {access_token}',
        'Accept': 'application/vnd.github+json',
        "X-GitHub-Api-Version": "2022-11-28"
    }
    response = requests.delete(url, headers=headers)

def handle_issue_comment_webhook(data, connection):
    comment = data.get("comment").get("body")
    action = data.get("action")
    issue_number = data.get("issue").get("number")
    original_user = frappe.session.user
    frappe.set_user(github_user)

    try:
        if action == "created":
            task = frappe.get_doc("Task", {"github_sync_github_issue_number": issue_number, "project": connection.project, "github_sync_with_github": 1})
            if task:
                task.add_comment("Comment", text=comment)
                task.save(ignore_permissions=True)
    except Exception as e:
        return "Error handling issue comment webhook: " + str(e)
    finally:
        frappe.set_user(original_user)

def handle_issue_webhook(data, connection):
    action = data.get("action")
    issue_number = data.get("issue").get("number")
    labels = [label['name'] for label in data.get('issue').get('labels', [])]
    original_user = frappe.session.user
    frappe.set_user(admin)

    try:
        task = frappe.db.exists("Task", {"github_sync_github_issue_number": issue_number, "project": connection.project, "github_sync_with_github": 1})
        if task and not action == "opened":
            task = frappe.get_doc("Task", {"github_sync_github_issue_number": issue_number, "project": connection.project, "github_sync_with_github": 1})
            task.description = data.get("issue").get("body")
            task.subject = data.get("issue").get("title")
            task.save(ignore_permissions=True)
        elif action == "opened" or (action in ["labeled", "unlabeled"] and "erpnext" in labels):
            last_task = frappe.get_last_doc("Task", {"github_sync_with_github": 1, "project": connection.project})
            subject = data.get("issue").get("title")
            github_sync_issue_index = last_task.github_sync_issue_index + 1 if last_task else 1
            task = frappe.get_doc({ 
                "doctype": "Task",
                "subject": f"[{connection.tasks_naming_series}-{github_sync_issue_index}] {subject}",
                "description": data.get("issue").get("body"),
                "project": connection.project,
                "github_sync_github_issue_number": issue_number,
                "github_sync_with_github": 1,
                "github_sync_issue_index": github_sync_issue_index,
                "github_sync_github_repo": connection.repository,
                "github_sync_github_user": connection.github_user,
            })
            task.save(ignore_permissions=True)
    except Exception as e:
        return "Error handling issue webhook: " + str(e)
    finally:
        frappe.set_user(original_user)
