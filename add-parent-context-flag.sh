#!/bin/bash

# Script to add page-use-parent-context flag to all Streaming version branches
# Usage: ./add-parent-context-flag.sh

set -e

# Define all branches to update
BRANCHES=(
  "feature/rename-streaming-main"
  "feature/rename-streaming-23.3"
  "feature/rename-streaming-24.1"
  "feature/rename-streaming-24.2"
  "feature/rename-streaming-24.3"
  "feature/rename-streaming-25.1"
  "feature/rename-streaming-25.2"
  "feature/rename-streaming-25.3"
)

echo "🚀 Starting to add page-use-parent-context flag to all Streaming branches..."
echo ""

for BRANCH in "${BRANCHES[@]}"; do
  echo "═══════════════════════════════════════════════════════════════"
  echo "📝 Processing branch: $BRANCH"
  echo "═══════════════════════════════════════════════════════════════"

  # Checkout the branch
  git checkout "$BRANCH"

  # Check if the flag already exists
  if grep -q "page-use-parent-context: true" antora.yml; then
    echo "✅ Flag already exists in $BRANCH, skipping..."
    echo ""
    continue
  fi

  # Add the flag after "attributes:" line
  # Using sed to insert the line
  sed -i '' '/^  attributes:$/a\
    page-use-parent-context: true
' antora.yml

  # Verify the change was made
  if grep -q "page-use-parent-context: true" antora.yml; then
    echo "✅ Successfully added flag to antora.yml"

    # Show the change
    echo "📄 Changes:"
    git diff antora.yml | head -15

    # Commit the change
    git add antora.yml
    git commit -m "Enable parent context navigation cards

Add page-use-parent-context flag to enable hierarchical navigation
with parent context cards in the UI. This shows the Self-Managed
parent card with Streaming/Connect subcards when viewing Streaming pages.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

    echo "✅ Committed changes to $BRANCH"
    echo ""
  else
    echo "❌ Failed to add flag to $BRANCH"
    echo ""
    exit 1
  fi
done

echo "═══════════════════════════════════════════════════════════════"
echo "✅ All branches updated successfully!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📤 Ready to push. Run the following commands to push all branches:"
echo ""
for BRANCH in "${BRANCHES[@]}"; do
  echo "git push origin $BRANCH"
done
echo ""
echo "Or push all at once with:"
echo "git push origin $(echo ${BRANCHES[@]})"
