# test_iis_github_actions
CI/CD step for siting server

## Hello app

A small FastAPI app with two server-rendered pages:

- `/`: the hello page, rendered from `templates/hello.html`.
- `/about`: a different page describing the application stack, rendered from
  `templates/about.html` using the shared hello layout.

Both pages include navigation links to switch between them.

With Python 3.10+ and [uv](https://docs.astral.sh/uv/) installed, run from
the repository root:

```sh
uv run uvicorn main:app --reload
```

Open http://127.0.0.1:8000/ to see “Hello, world!”.
Open http://127.0.0.1:8000/about to see the about page.

The template response passes `request` inside its context for compatibility with
the older Starlette template API on the existing IIS Python environment.

### Configurable router prefix

Set `ROUTER_PREFIX` in the application's environment before starting it:

```powershell
$env:ROUTER_PREFIX = "/api"
uv run uvicorn main:app --reload
```

The hello page is then available at http://127.0.0.1:8000/api/.
The about page is available at http://127.0.0.1:8000/api/about, and navigation
links automatically include the prefix.
The default is an empty prefix, preserving `/`. A nonempty prefix must start
with `/` and must not end with `/`; invalid values fail at startup.
The API documentation stays at `/docs`.

For IIS, set this variable in the environment of the actual Python process
(not just the deployment runner) and restart that process. `.env` files are not
loaded automatically. If IIS strips a proxy prefix before forwarding requests,
use Uvicorn's `--root-path` for that proxy mount instead of adding it again as
`ROUTER_PREFIX`.

## Deploy to an existing IIS site

The [IIS deployment workflow](.github/workflows/deploy-iis.yml) runs on pushes to
`main` or manually from **Actions > Deploy to IIS > Run workflow**:

1. **Build** on `ubuntu-latest`: package `main.py`, `templates`, and
   `pyproject.toml` from the commit into `app.zip` and upload it as an artifact.
2. **Approval**: wait for a required reviewer of the `production` environment
   to approve the deployment.
3. **Deploy**, with `needs: build`, on the self-hosted Windows IIS runner:
   after approval, download and extract the ZIP, copy it into
   `E:\inetpub\wwwroot\test_iis_github_actions`, and recycle the app's pool.

The workflow does not create or reconfigure IIS sites.

### One-time workflow configuration

1. Register the server's runner with this repository under **Settings > Actions >
   Runners** and add the custom label `iis`. Run it as a service.
2. Give the runner service account permission to manage IIS application pools
   and write to the site's physical directory. The IIS PowerShell
   `WebAdministration` module must be installed.
3. Under **Settings > Secrets and variables > Actions > Variables**, create
   `IIS_APP_POOL_NAME` with the exact existing application pool name. No deployment password
   is needed because the runner runs on the server.
4. Ensure the target folder belongs to this app and `IIS_APP_POOL_NAME` is its
   dedicated pool. The workflow does not infer a site from the folder or validate
   its IIS mapping. Recycling a shared pool affects every app using it.
5. Before enabling or running the updated workflow, go to **Settings >
   Environments**, create or open `production`, and configure:
   - Under **Deployment protection rules**, enable **Required reviewers** and
     select the user or team allowed to approve deployments. Only one selected
     reviewer needs to approve.
   - Enable **Prevent self-review** if the person triggering the workflow must
     not approve their own deployment.
   - Disable **Allow administrators to bypass configured protection rules** if
     approvals must also be enforced for administrators.
   - Under **Deployment branches and tags**, choose **Selected branches and
     tags** and add a branch rule for `main`. This also prevents a manually
     triggered run from deploying another branch.

The workflow's `environment: production` reference does not configure reviewers.
If the environment is missing, GitHub can create it without protection rules,
and deployment will not pause. Configure and save the environment in GitHub
before relying on this approval gate. Availability of required reviewers depends
on the repository visibility and GitHub plan; if the option is unavailable, this
workflow alone cannot enforce approval.

### Approving a deployment

Push to `main` as usual. The build runs automatically; once it succeeds, the
deployment waits for environment approval before starting work on the IIS runner.
An authorized reviewer opens **Actions > Deploy to IIS > the workflow run >
Review deployments**, selects `production`, and chooses **Approve and deploy**.
Rejecting the deployment prevents the IIS deployment job from running.

The same approval gate applies to **Run workflow** executions. This does not
change who can push or merge into `main`; branch protection is separate. Users
who can change workflows or environment settings can change this gate, so restrict
those permissions if approval must not be bypassed.

### Deployment behavior

- Requires the target directory to exist and the configured pool to be running.
- Copies only the packaged application files into the app's target folder, then
  recycles only the configured application pool after a successful copy.
  Other site folders under `wwwroot` are not modified; IIS is not restarted.
- Preserves `web.config`, `.env` / `.env.*`, virtual environments, and server-only
  files. Git metadata, workflow files, Python caches, and the README are not
  deployed. Copying is additive: files removed from Git are not removed from IIS.
- Reuses the existing Python runtime and installed dependencies. Changes to
  `pyproject.toml` do **not** install dependencies; update the server environment
  separately before deploying code that needs new packages.
- Copies while the pool is running to keep deployment lightweight. This is not
  atomic: requests can see mixed versions during copying, and locked files can
  cause deployment to fail. Copy failures skip recycling and require redeployment.
- Removes the downloaded ZIP and extracted temporary files after the deploy step.
- Assumes IIS manages the application's process. If IIS only reverse-proxies to
  an independently managed Uvicorn service, that service needs its own restart
  step; restarting the IIS pool will not restart it.

Only allow trusted code and users to run workflows on this runner, especially
when its account has elevated IIS permissions. Do not enable untrusted
pull-request workflows on the server.

### Placeholder IIS configuration

The repository's [web.config](web.config) is a minimal, valid XML placeholder,
not a working FastAPI hosting configuration. Keep the existing server-side
configuration; the deployment workflow excludes this file from copying.
