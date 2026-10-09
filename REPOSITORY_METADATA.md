# GitHub repository identity

The application is named **Universal Koei Tecmo Save Editor**. Repository
settings are stored on GitHub; changing a README or pushing code does not change
the repository name or About section.

Prepared settings:

- Repository name: `Universal-Koei-Tecmo-Save-Editor`
- Description: `A free Windows save editor by Mexican for Dynasty Warriors, Pirate Warriors and Atelier. One executable, separate game/platform editors, backups, Undo and Save As. Contributions welcome.`
- Website: `https://github.com/MMexicann/Universal-Koei-Tecmo-Save-Editor/blob/main/CONTRIBUTING.md`

The cloud session can push code but its requests to `api.github.com` return
`Forbidden`, including the repository-settings update. These settings have not
been applied. The owner can set the name in **Settings → General**, and the
description and website using the **About** gear on the repository homepage.

Alternatively, run this with GitHub CLI from a session that can administer the
repository:

```sh
gh api --method PATCH repos/MMexicann/DW3-Remastered-Save-Editor \
  -f name=Universal-Koei-Tecmo-Save-Editor \
  -f description='A free Windows save editor by Mexican for Dynasty Warriors, Pirate Warriors and Atelier. One executable, separate game/platform editors, backups, Undo and Save As. Contributions welcome.' \
  -f homepage=https://github.com/MMexicann/Universal-Koei-Tecmo-Save-Editor/blob/main/CONTRIBUTING.md
```

After a successful rename, update the local `origin` and current documentation
links to the confirmed new URL. Existing releases and tags stay with the
repository; there is no need to recreate v1.1 or v1.2. The README and release
notes already link the contributor and AI-agent guides under the current URL.
