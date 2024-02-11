import frappe

def after_install():
    github_user = {
        "first_name": "Github User",
        "email": "githubuser@example.com",
    }
    if not frappe.db.exists('User', {"email": github_user.get("email")}):
        user = frappe.get_doc({
            "doctype": "User",
            "email": github_user.get("email"),
            "first_name": github_user.get("first_name"),
            "enabled": 1,
        })
        user.insert(ignore_permissions=True)
        frappe.db.commit()