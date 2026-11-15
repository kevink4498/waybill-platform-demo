# Architecture

## Request path

1. A hub scanner posts a scan to `ingest-api` through the shared Gateway (TLS terminates there).
2. `ingest-api` validates and normalises the event, then publishes it to the `scan-events` topic.
   It authenticates as its own GCP service account through Workload Identity.
3. Pub/Sub delivers each message two ways:
   - a **push subscription** to `tracker-worker`, signed with an OIDC token, which updates parcel state;
   - a **BigQuery subscription** that lands the raw message in `waybill_raw.scan_events_raw`.
4. A message that `tracker-worker` rejects five times goes to `scan-events-dlq`, where a holding
   subscription keeps it for 14 days.

## Why tracker-worker is written the way it is

Pub/Sub guarantees at-least-once delivery and no ordering. The worker therefore treats a
redelivered scan as a duplicate, ignores scans that are older than the stored state, and never
moves a parcel out of `DELIVERED`. Those rules are the unit tests in
`services/tracker-worker/tests/test_tracker.py`. A malformed message returns HTTP 400 so Pub/Sub
stops retrying it and dead-letters it instead of blocking the subscription.

## Environments

| | dev | staging | prod |
| --- | --- | --- | --- |
| Replicas (min–max) | 1–2 | 1–3 | 2–6 |
| PodDisruptionBudget | off | off | on |
| Raw data retention | 30 days | 90 days | 365 days |
| BigQuery deletion protection | off | off | on |
| Terraform apply | on merge | on merge | on merge, after approval |

Everything else is identical: same chart version range, same Terraform modules.

## Security model

| Concern | Control |
| --- | --- |
| Cloud credentials in pods | GKE Workload Identity; `automountServiceAccountToken` is off unless a GCP identity is bound |
| Cloud credentials in CI | GitHub OIDC to a Workload Identity provider; no stored keys |
| Application secrets | Vault KV v2, synced by the Vault Secrets Operator; pods restart when a secret rotates |
| Non-sensitive config | ConfigMap from Helm values; a checksum annotation rolls pods on change |
| Network | Namespace default-deny; per-release ingress from the gateway namespace, egress to DNS and 443 |
| Pod hardening | Pod Security `restricted`: non-root, read-only root filesystem, all capabilities dropped, seccomp `RuntimeDefault` |
| IAM | Roles bound on the topic and dataset, never on the project |
| Supply chain | Pinned dependencies and actions, Dependabot updates, Trivy scan gates the push, no `pip` in the runtime image, immutable tags enforced in CI |

## Known limits

- Parcel state is held in memory to keep the sample small. A real deployment would back
  `ParcelStore` with a database; the interface is the seam for that.
- The chart assumes HTTP services. A queue-only worker would need a variant without a Service.
- Egress on 443 is open to any address. Tightening it to Google API ranges and the Vault address
  is the next step, using `networkPolicy.egress.extraCidrs` or an FQDN-aware policy engine.
