# 4. No package manager in the runtime image

**Context.** The first image scan on `main` failed on CVE-2025-47273 in `setuptools 70.3.0`,
although the image's own `setuptools` was current. The finding came from the copy that `pip`
vendors internally and declares in `pip/_vendor/bom.cdx.json`. Upgrading `setuptools` could not
clear it, because the vulnerable copy belongs to `pip`.

**Decision.** Dependencies are installed in the build stage and copied across; the final stage
then removes `pip` and `setuptools`. The services never install anything at runtime.

**Why.** It removes the finding at its source instead of adding a scanner exception, and it
shrinks what an attacker could use inside a compromised container. An ignore rule would have
hidden this CVE and every later one in the same vendored tree.

**Cost.** Nobody can `pip install` a debugging tool into a running pod. Debugging uses an
ephemeral container (`kubectl debug`) instead, which is the better habit with a read-only root
filesystem anyway.

**How it was found.** The scan step prints each finding as a run annotation with the package,
installed version and fixed version, so the cause was visible on the run page without opening
logs.
