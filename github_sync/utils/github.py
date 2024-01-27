import frappe
import requests
import json
from frappe import _
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

def create_github_issue(doc, connection):
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
        issue_number = response.json().get("number")
        doc.github_sync_github_user = connection.github_user
        doc.github_sync_github_repo = connection.repository
        doc.github_sync_github_issue_number = issue_number
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
        'body': doc.description
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
    if not response.ok:
        frappe.throw(_("Error deleting webhook: " + response.text), title="Error")