// Copyright (c) 2024, Ashish and contributors
// For license information, please see license.txt

frappe.ui.form.on("Github Connection", {
  refresh(frm) {
    frm.page.wrapper
      .find('button[data-fieldname="github_login"]')
      .html(function () {
        return (
          '<img src="https://cdn.discordapp.com/attachments/937628023497297930/988735284504043520/github.png" style="margin-right: 8px; width: 16px; height: 16px; border-radius: 8px;">' +
          $(this).text()
        );
      })
      .addClass("btn-primary");
  },
  async onload(frm) {
    const access_token = frappe.get_cookie("github_access_token");
    if (access_token) {
      const headers = {
        Authorization: `token ${access_token}`,
      };
      const response = await fetch("https://api.github.com/user/repos", {
        headers,
      });
      if (!response.ok) {
        frappe.msgprint({
          title: __("Error"),
          message: __("Invalid access token. Please login again."),
          indicator: "red",
        });
        return;
      }
      const userResponse = await fetch("https://api.github.com/user", {
        headers,
      });
      const userData = await userResponse.json();
      const repos = await response.json();
      if (repos.length < 0) {
        frappe.msgprint("No repositories found");
        return;
      }
      frm.set_value("github_user", userData.login);
      const options = repos.map((repo) => repo.name);
      frm.set_df_property("repository", "options", options);
      frm.refresh_field("repository");
      frm.refresh_field("github_user");
    }
  },
  async github_login(frm) {
    const response = await frappe.call({
      method: "github_sync.github_sync.api.get_config",
      args: { key: "github_client_id" },
    });
    const CLIENT_ID = response.message;
    const REDIRECT_URI =
      "http://localhost:8000/api/method/github_sync.github_sync.api.callback";
    const SCOPES = "repo";
    window.open(
      `https://github.com/login/oauth/authorize?client_id=${CLIENT_ID}&redirect_uri=${REDIRECT_URI}&scope=${encodeURIComponent(
        SCOPES
      )}`,
      "_self"
    );
  },
  before_save: function (frm) {
    frm.set_value(
      "github_access_token",
      frappe.get_cookie("github_access_token")
    );
  },
  github_logout() {
    frappe.call({
      method: "github_sync.github_sync.api.github_logout",
    });
  },
});
