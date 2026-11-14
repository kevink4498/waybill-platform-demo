# 3. Promote by pull request, with immutable tags

**Decision.** Moving a build from one environment to the next is a pull request that changes
`image.tag` in that environment's overlay. Tags must match `main-<sha>` or `vX.Y.Z`.

**Why.** The same artifact that was tested in staging is what reaches prod, the approval is the
PR review, and the audit trail is the Git log. Rejecting `latest` and branch tags removes the
case where two pods of one release run different code.

**Cost.** One extra PR per promotion. The `promote` workflow creates it, so the manual work is a
review and a merge.
