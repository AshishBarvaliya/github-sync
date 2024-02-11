# Copyright (c) 2024, Ashish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from github_sync.utils.github import delete_github_webhook


class GithubConnection(Document):
	def validate(self):
		if not self.is_new() and (self.has_value_changed('github_user') or self.has_value_changed('repository') or self.has_value_changed('project') or self.has_value_changed('github_access_token') or self.has_value_changed('github_webhook_id') or self.has_value_changed('github_webhook_secret')):
			frappe.throw(_('You cannot change Github User, Repository, Project, Github Access Token, Github Webhook Secret or Github Webhook ID after creation'))
	def on_trash(self):
		delete_github_webhook(self.github_webhook_id, self.repository, self.github_user, self.github_access_token)
