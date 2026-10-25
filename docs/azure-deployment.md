# Azure trial deployment handoff

Deployment is prepared, **not live**. The user has not completed Azure registration; no subscription, resource group, app, model deployment or paid service has been created by this task. Azure CLI and Docker were not present locally. Complete account/identity/terms steps personally; do not send passwords or API keys to chat.

## Trial path and cost boundaries

The supplied ARM template creates only an Azure App Service Linux **F1 Free** plan and a Python app. It has no paid-SKU fallback, registry, storage account or model deployment. F1 availability depends on subscription/region/quota. Unsupported F1 provisioning must stop, not silently switch to a paid tier.

Microsoft currently lists F1 as 60 shared CPU minutes/day, 1 GB RAM and 1 GB storage, intended for trials/learning with no SLA. It does **not** guarantee the hackathon's uninterrupted availability. Model requests in Foundry are a separate service and are not made free by hosting on F1. Check subscription credits and model prices before enabling them.

Sources: [App Service Linux pricing](https://azure.microsoft.com/en-us/pricing/details/app-service/linux/), [Python deployment](https://learn.microsoft.com/en-us/azure/app-service/quickstart-python), [Python runtime and startup configuration](https://learn.microsoft.com/en-us/azure/app-service/configure-language-python).

## Ready before account setup

- `deploy/azure/main.json`: ARM template, F1-only, HTTPS, FTP disabled, no always-on, model calls disabled.
- `deploy/azure/start.sh`: custom Python demo-server startup on port 8000. Private state is `/home/nextplay`, outside static code. Quota survives app process restarts when App Service persistent home storage is available.
- `scripts/build_azure_package.py`: curated code/data ZIP and manifest. Excludes keys, uploaded videos, human labels, Git, dependency caches, duplicate league and large raw `decisions.jsonl`; B already reads its immutable sidecar snapshots and explicitly permits missing raw decisions. The four full tracking matches are retained.
- `/healthz`: no-secret health endpoint for warmup and smoke tests.

This is still the existing standard-library HTTP demo server behind the managed platform endpoint, not a production-grade serving stack. Private real-video review should stay local until proper authentication and retention controls are added. The cloud judging version defaults to **synthetic data**, `NEXTPLAY_VIDEO_UPLOADS=0` and `NEXTPLAY_DAILY_MODEL_CALLS=0`.

## Steps after registration

1. Confirm an active subscription and free-credit status in the Azure portal. Choose an existing resource group in a region that supports Linux F1. The deploy script deliberately does not create an unspecified resource group.
2. Install official Azure CLI, or use Azure Cloud Shell. Sign in locally with `az login`; select the intended subscription. Authentication is interactive and credentials stay out of the repository.
3. Check supported Python runtime with `az webapp list-runtimes --os linux`; the template requests Python 3.12. If unavailable, explicitly review and update the template rather than guessing a paid fallback.
4. Build and inspect the package locally:

   ```sh
   python3 scripts/build_azure_package.py
   ```

5. Preview the actual resource changes using the existing resource group and chosen globally unique app name:

   ```sh
   sh deploy/azure/deploy.sh EXISTING_GROUP UNIQUE_APP_NAME artifacts/deployment/nextplay-azure.zip
   ```

6. After reviewing the what-if output, the same script with `--apply` provisions F1 and uploads the ZIP:

   ```sh
   sh deploy/azure/deploy.sh EXISTING_GROUP UNIQUE_APP_NAME artifacts/deployment/nextplay-azure.zip --apply
   ```

7. Open the actual returned HTTPS URL. Verify `/healthz`, the league page, the three current-match cases, counterfactual reset, English default and a phone-width layout. A successful CLI command alone is not deployment acceptance.
8. Separately deploy a Responses/function-calling/structured-output-capable model in Foundry if account access and budget allow. Set `NEXTPLAY_MODEL_BASE_URL`, deployment name and API key in App Service server environment variables. Do not put the key in HTML, repository, screenshots or this document. Set a deliberately small nonzero `NEXTPLAY_DAILY_MODEL_CALLS` only after checking the credits and quota.
9. Run one genuine provider tool-call/evidence-review smoke test and record sanitized trace. Then execute `scripts/evaluate_agents.py --live` on the intended environment if budget permits. Until then, describe the integration as implemented but not provider-tested.

The package has only been locally assembled/tested. Actual ARM validation, resource availability, startup on Azure, Foundry authentication, billing and public-URL verification require the account and remain open.
