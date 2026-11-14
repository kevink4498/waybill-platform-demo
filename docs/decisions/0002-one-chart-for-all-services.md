# 2. One shared chart instead of a chart per service

**Decision.** Every HTTP service is deployed with `charts/microservice`. Services differ only in
values.

**Why.** Security settings (security context, NetworkPolicy, probes, Workload Identity) are
defined once, so a fix reaches every service by bumping one chart version. Adding a service is a
few lines of YAML.

**Cost.** The chart has to stay generic. A service with unusual needs gets a feature flag in the
chart or, if that would distort it, its own chart. The version range `0.1.x` in each HelmRelease
means patch releases roll out everywhere; a breaking change needs a minor bump and a deliberate
update per environment.
