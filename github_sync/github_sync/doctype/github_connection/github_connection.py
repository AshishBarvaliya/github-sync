# Copyright (c) 2024, Ashish and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from github_sync.utils.github import delete_github_webhook


class GithubConnection(Document):
	def on_trash(self):
		delete_github_webhook(self.github_webhook_id, self.repository, self.github_user, self.github_access_token)
