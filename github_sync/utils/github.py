from urllib.parse import urlparse
import frappe
import requests
import json
from frappe import _
import markdown
from bs4 import BeautifulSoup
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
import re
import os

github_user="githubuser@example.com"
admin="Administrator"

def fetch_image_and_save(image_url):
    pattern = r'https?://github\.com/([^/]+)/([^/]+)'
    match = re.search(pattern, image_url)
    if not match:
        return "Invalid Url"
    
    username, repo = match.groups()
    connection = frappe.db.get_value("Github Connection", {"repository": repo, "github_user": username}, ["github_access_token"], as_dict=1)
    if connection:
        headers = {
            'Authorization': f'token {connection.github_access_token}',
            'Accept': 'application/vnd.github+json',
            "X-GitHub-Api-Version": "2022-11-28"
        }
        parsed_url = urlparse(image_url)
        filename = os.path.basename(parsed_url.path) + '.png'
        
        directory_path = frappe.get_site_path('public', 'files', 'github_sync', repo)
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)  
        
        public_file_path = os.path.join(directory_path, filename)
        if os.path.exists(public_file_path):
            file_url = f"/files/github_sync/{repo}/{filename}"
            return file_url
        
        response = requests.get(image_url, headers=headers)
        if response.status_code == 200:
            with open(public_file_path, 'wb') as file:
                file.write(response.content)
            file_url = f'/files/github_sync/{repo}/{filename}'
            return file_url
        else:
            return "Failed to fetch image from GitHub"
    
    return "GitHub Access Token Not Found"

class EnhancedMarkdownExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(EnhancedMarkdownPreprocessor(md), 'enhanced_markdown_preprocessor', 175)

class EnhancedMarkdownPreprocessor(Preprocessor):
    def run(self, lines):
        new_lines = []
        in_code_block = False
        code_block_lines = []
        code_block_language = None

        for line in lines:
            # Handle code blocks
            if line.startswith('```'):
                if in_code_block:
                    # Ending a code block
                    pre_tag = '<pre class="ql-code-block-container" spellcheck="false"'
                    if code_block_language:
                        pre_tag += f' data-language="{code_block_language}"'
                    pre_tag += '>'
                    new_lines.append(pre_tag + '\n'.join(code_block_lines) + '</pre>')
                    in_code_block = False
                    code_block_lines = []
                    code_block_language = None
                else:
                    in_code_block = True
                    code_block_language = line.strip('```').strip()
                    continue
            elif in_code_block:
                code_block_lines.append(f'<div class="ql-code-block">{line}</div>')
                continue

            elif re.match(r'!\[(.*?)\]\((.*?)\)', line):
                image_match = re.match(r'!\[(.*?)\]\((.*?)\)', line)
                alt_text = image_match.group(1)
                image_url = image_match.group(2)
                saved_image = fetch_image_and_save(image_url)
                new_line = f'<img src="{saved_image}" alt="{alt_text}">'
                new_lines.append(new_line + '  ')
                continue
            
            elif re.match(r'^#[^ ]', line):
                content = line.lstrip('#').strip()
                new_line = f'<p><a href="http://google.com" rel="noopener noreferrer">{content}</a></p>'
                new_lines.append(new_line + '  ')
                continue

            # Handle task lists
            elif re.match(r'- \[ \] .+', line):
                line = f'<li data-list="unchecked"><span class="ql-ui" contenteditable="false"></span>{line[5:]}</li>'
            elif re.match(r'- \[x\] .+', line) or re.match(r'- \[X\] .+', line):
                line = f'<li data-list="checked"><span class="ql-ui" contenteditable="false"></span>{line[5:]}</li>'

            else:
                new_lines.append(line + '  ')

        return new_lines

def markdown_to_html(md_text):
    md_text = re.sub(r'(\n\s*\n)', r'\n\n<br>\n\n', md_text)  # Handle paragraphs with breaks
    md = markdown.Markdown(extensions=[EnhancedMarkdownExtension(), 'markdown.extensions.extra'])
    html = md.convert(md_text)
    return html

def create_github_issue(doc, connection):
    url = f"https://api.github.com/repos/{connection.github_user}/{connection.repository}/issues"
    headers = {
        'Authorization': f'token {connection.github_access_token}',
        'Accept': 'application/vnd.github+json',
        "X-GitHub-Api-Version": "2022-11-28"
    }
    data = {
        'title': doc.subject,
        'body': doc.github_sync_github_description if doc.github_sync_github_description else "",
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
        'body': doc.github_sync_github_description if doc.github_sync_github_description else "",
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
    requests.delete(url, headers=headers)

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

    html = markdown_to_html(data.get("issue").get("body"))

    soup = BeautifulSoup(html, 'html.parser')
    ql_editor_html = BeautifulSoup('<div class="ql-editor read-mode"></div>', 'html.parser').div
    ql_editor_html.append(soup)

    try:
        task = frappe.db.exists("Task", {"github_sync_github_issue_number": issue_number, "project": connection.project, "github_sync_with_github": 1})
        if task and not action == "opened":
            task = frappe.get_doc("Task", {"github_sync_github_issue_number": issue_number, "project": connection.project, "github_sync_with_github": 1})
            task.description = str(ql_editor_html)
            task.github_sync_github_description = data.get("issue").get("body")
            task.subject = data.get("issue").get("title")
            task.save(ignore_permissions=True)
        elif action == "opened" or (action in ["labeled", "unlabeled"] and "erpnext" in labels):
            last_task = frappe.get_last_doc("Task", {"github_sync_with_github": 1, "project": connection.project})
            subject = data.get("issue").get("title")
            github_sync_issue_index = last_task.github_sync_issue_index + 1 if last_task else 1
            task = frappe.get_doc({ 
                "doctype": "Task",
                "subject": f"[{connection.tasks_naming_series}-{github_sync_issue_index}] {subject}",
                "description": str(ql_editor_html),
                "github_sync_github_description": data.get("issue").get("body"),
                "project": connection.project,
                "github_sync_github_issue_number": issue_number,
                "github_sync_with_github": 1,
                "github_sync_issue_index": github_sync_issue_index,
                "github_sync_github_repo": connection.repository,
                "github_sync_github_user": connection.github_user,
            })
            task.save(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        return "Error handling issue webhook: " + str(e)
    finally:
        frappe.set_user(original_user)
