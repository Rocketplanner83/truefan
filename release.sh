#!/bin/bash
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <version>"
  exit 1
fi

VERSION=$1
IMAGE="rocketplanner83/truefan"

echo "🚀 Releasing TrueFan v$VERSION"

# Ensure git is clean
if ! git diff-index --quiet HEAD --; then
  echo "⚠️  You have uncommitted changes. Commit or stash them first."
  exit 1
fi

# Commit, tag, and push
git add .
git commit -m "Release v$VERSION"
git tag -a "v$VERSION" -m "Release v$VERSION"
git push origin main --tags

# Build and push Docker images
docker build -t $IMAGE:$VERSION .
docker push $IMAGE:$VERSION

docker tag $IMAGE:$VERSION $IMAGE:latest
docker push $IMAGE:latest

echo "✅ Release v$VERSION complete!"
