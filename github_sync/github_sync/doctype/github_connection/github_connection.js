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
      const response = await fetch("https://api.github.com/user/repos", {
        headers: {
          Authorization: `token ${access_token}`,
        },
      });

      if (!response.ok) {
        frappe.set_cookie("github_access_token", null);
        frappe.msgprint("Invalid access token. Please login again.");
        return;
      }
      const repos = await response.json();
      console.log(repos);
      if (repos.length < 0) {
        frappe.msgprint("No repositories found");
        return;
      }
      frm.set_value("github_user", repos[0].owner.login);
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
    window.open(
      `https://github.com/login/oauth/authorize?client_id=${CLIENT_ID}&redirect_uri=${REDIRECT_URI}`,
      "_self"
    );
  },
});
