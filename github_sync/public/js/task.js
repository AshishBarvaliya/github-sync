frappe.ui.form.on("Task", {
  onload(frm) {
    if (frm.doc.project) {
      frappe.db.get_value(
        "Github Connection",
        { project: frm.doc.project },
        ["repository"],
        (r) => {
          if (r && r.repository) {
            frm.set_df_property("github_sync_with_github", "hidden", 0);
          }
        }
      );
    }
  },
  project(frm) {
    if (frm.doc.project) {
      frappe.db.get_value(
        "Github Connection",
        { project: frm.doc.project },
        ["repository"],
        (r) => {
          if (r && r.repository) {
            frm.set_df_property("github_sync_with_github", "hidden", 0);
            frm.set_value("github_sync_with_github", 1);
          } else {
            frm.set_df_property("github_sync_with_github", "hidden", 1);
            frm.set_value("github_sync_with_github", 0);
          }
        }
      );
    } else {
      frm.set_df_property("github_sync_with_github", "hidden", 1);
      frm.set_value("github_sync_with_github", 0);
    }
  },
});
