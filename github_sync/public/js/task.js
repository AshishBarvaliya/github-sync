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
  before_save(frm) {
    if (frm.doc.description) {
      if (window.turndownServiceObject) {
        frm.set_value(
          "github_sync_github_description",
          window.turndownServiceObject.turndown(frm.doc.description)
        );
      } else {
        $.ajax({
          url: "https://cdnjs.cloudflare.com/ajax/libs/turndown/7.0.0/turndown.js",
          dataType: "script",
          success: () => {
            if (window.TurndownService) {
              const turndownService = new window.TurndownService();
              turndownService.addRule("paragraphs", {
                filter: "p",
                replacement: function (content) {
                  return "\n" + content + "\n";
                },
              });
              turndownService.addRule("heading", {
                filter: ["h1"],
                replacement: function (content) {
                  return "# " + content + "\n\n";
                },
              });
              turndownService.addRule("heading", {
                filter: ["h2"],
                replacement: function (content) {
                  return "## " + content + "\n\n";
                },
              });
              turndownService.addRule("quillCodeBlock", {
                filter: function (node) {
                  return (
                    node.nodeName === "PRE" &&
                    node.classList.contains("ql-code-block-container")
                  );
                },
                replacement: function (_content, node) {
                  var codeContent = "";
                  var codeBlock = node.querySelector(".ql-code-block");
                  if (codeBlock) {
                    codeContent = codeBlock.textContent || codeBlock.innerText;
                  }
                  return "\n```\n" + codeContent + "\n```\n";
                },
              });

              turndownService.addRule("checkList", {
                filter: function (node) {
                  return (
                    node.nodeName === "LI" &&
                    node.hasAttribute("data-list") &&
                    (node.getAttribute("data-list") === "checked" ||
                      node.getAttribute("data-list") === "unchecked")
                  );
                },
                replacement: function (content, node) {
                  const isChecked =
                    node.getAttribute("data-list") === "checked";
                  return isChecked
                    ? `- [x] ${content.trim()} \n`
                    : `- [ ] ${content.trim()} \n`;
                },
              });

              turndownService.addRule("quillBulletList", {
                filter: function (node) {
                  return (
                    node.nodeName === "LI" &&
                    node.hasAttribute("data-list") &&
                    node.getAttribute("data-list") === "bullet"
                  );
                },
                replacement: function (content) {
                  return `- ${content} \n`;
                },
              });

              turndownService.addRule("imageWithLink", {
                filter: "img",
                replacement: function (_content, node) {
                  const src = node.getAttribute("src");
                  const domain = window.location.origin;
                  const fullPath = src.startsWith("http") ? src : domain + src;
                  return `![${fullPath}](${fullPath})`;
                },
              });

              turndownService.addRule("leaveTableAsHtml", {
                filter: ["table"],
                replacement: function (_content, node) {
                  return node.outerHTML;
                },
              });

              const markdown = turndownService.turndown(frm.doc.description);
              frm.set_value("github_sync_github_description", markdown);
              window.turndownServiceObject = turndownService;
            }
          },
        });
      }
    }
  },
});
