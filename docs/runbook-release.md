# Release runbook

## Ship a change

1. Merge the service change to `main`. The `services` workflow pushes `main-<sha>`.
2. Run the **promote** workflow: target `dev`, tag `main-<sha>`. Merge the PR it opens.
3. Check the rollout: `flux get helmreleases -n waybill` shows `Ready=True` at the new revision.
4. Promote onwards by copying: target `staging`, from `dev`; later target `prod`, from `staging`.

## Roll back

Revert the promotion PR and merge the revert. Flux applies the previous tag. Do not
`helm rollback` by hand: Flux would undo it at the next reconcile.

## A release is stuck

| Symptom | Likely cause | Check |
| --- | --- | --- |
| `HelmRelease` not ready, "chart not found" | Chart version not published | `platform` workflow on `main`; bump `version` in `Chart.yaml` |
| Pods `ImagePullBackOff` | Tag was never pushed (PR build) or registry auth | `services` workflow run for that commit |
| Pods `CreateContainerConfigError` | Vault secret not synced | `kubectl get vaultstaticsecret -n waybill`; check the Vault path in the overlay |
| Pods `Pending` | ResourceQuota exhausted | `kubectl describe quota -n waybill` |
| 5xx from Pub/Sub push | NetworkPolicy or route change | `kubectl get httproute,networkpolicy -n waybill` |

## Replay dead-lettered messages

Inspect with `gcloud pubsub subscriptions pull scan-events-dlq-hold --limit=10`, fix the cause,
then republish the payloads to `scan-events`. The worker is idempotent, so replaying a message
that was already applied is safe.
