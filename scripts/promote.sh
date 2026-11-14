#!/usr/bin/env bash
# Promote an image tag into an environment overlay. The change is a Git commit, so every
# release is reviewed in a pull request and Flux does the actual deployment.
#
#   scripts/promote.sh <env> <service|all> <tag>
#   scripts/promote.sh staging all --from dev      # copy whatever dev is running
set -euo pipefail

usage() { echo "usage: $0 <dev|staging|prod> <ingest-api|tracker-worker|all> <tag | --from <env>>" >&2; exit 2; }

[ $# -ge 3 ] || usage
target="$1"; service="$2"; shift 2
root="$(cd "$(dirname "$0")/.." && pwd)/gitops/apps/overlays"
[ -d "$root/$target" ] || { echo "unknown environment: $target" >&2; exit 2; }

case "$service" in
  all) services=(ingest-api tracker-worker) ;;
  ingest-api|tracker-worker) services=("$service") ;;
  *) usage ;;
esac

source_env=""
tag=""
if [ "$1" = "--from" ]; then
  [ $# -eq 2 ] || usage
  source_env="$2"
  [ -d "$root/$source_env" ] || { echo "unknown environment: $source_env" >&2; exit 2; }
else
  tag="$1"
fi

for svc in "${services[@]}"; do
  file="$root/$target/$svc.yaml"
  new="$tag"
  if [ -n "$source_env" ]; then
    new="$(yq -r '.spec.values.image.tag' "$root/$source_env/$svc.yaml")"
  fi
  # Mutable tags make a deployment untraceable; refuse them.
  if [[ ! "$new" =~ ^(main-[0-9a-f]{7,40}|v[0-9]+\.[0-9]+\.[0-9]+)$ ]]; then
    echo "refusing non-immutable tag '$new' for $svc (expected main-<sha> or vX.Y.Z)" >&2
    exit 1
  fi
  old="$(yq -r '.spec.values.image.tag' "$file")"
  if [ "$old" = "$new" ]; then
    echo "$target/$svc already at $new"
    continue
  fi
  sed -i -E "s|^(      tag: ).*$|\1$new|" "$file"
  echo "$target/$svc: $old -> $new"
done
