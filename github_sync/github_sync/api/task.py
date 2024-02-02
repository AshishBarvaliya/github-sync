import frappe
from frappe import _
import requests
import json
from github_sync.utils.github import create_github_issue, update_github_issue 

@frappe.whitelist()
def on_update(doc, method, *args, **kwargs):
    if doc.project:
        connection = frappe.db.get_value("Github Connection", {"project": doc.project}, ["github_user", "repository", "github_access_token"], as_dict=1)
        if connection and doc.github_sync_with_github == 1:
            if doc.github_sync_github_issue_number:
                if doc.github_sync_github_user == connection.github_user and doc.github_sync_github_repo == connection.repository:
                    update_github_issue(doc, connection)
                else:
                    doc.github_sync_github_issue_number = None
            else:
                try:
                    last_task = frappe.get_last_doc("Task", {"github_sync_with_github": 1, "project": doc.project})
                    if last_task and last_task.github_sync_issue_index:
                        doc.github_sync_issue_index = last_task.github_sync_issue_index + 1
                    else:
                        doc.github_sync_issue_index = 1
                except frappe.DoesNotExistError:
                        doc.github_sync_issue_index = 1
                doc.subject = f"[{connection.tasks_naming_series}-{doc.github_sync_issue_index}] {doc.subject}"
                create_github_issue(doc, connection)