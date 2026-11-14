# 1. Deploy by pull (Flux), not by push from CI

**Decision.** CI publishes images and charts. FluxCD in each cluster pulls the desired state from
`gitops/` and applies it. CI holds no cluster credentials.

**Why.** A push model gives the CI system admin access to every cluster and makes "what is
deployed" a question about pipeline history. With pull, the cluster's state is whatever `main`
says, drift is corrected automatically, and a compromised pipeline cannot reach production.

**Cost.** A release takes up to one reconcile interval to appear, and debugging needs
`flux get helmreleases` rather than a pipeline log. Both are acceptable here.
