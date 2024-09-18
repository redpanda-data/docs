#!/bin/bash

# Script to automate the setup of author mode (https://docs.antora.org/antora/latest/playbook/author-mode/) with multiple worktrees in Antora.
# Takes multiple GitHub repository names as arguments and clones the repos in the local workspace.

WORKSPACE_DIR="workspace"
ORG="redpanda-data"
DEFAULT_BRANCH="main"  # Default main branch

show_help() {
  echo
  echo "Usage: $0 <repo_name_1> <repo_name_2> ... <repo_name_N>"
  echo
  echo "Purpose:"
  echo "  This script allows you to set up author mode in Antora, where all content from the specified"
  echo "  repositories is cloned locally into a workspace. This lets you work on multiple repositories"
  echo "  and branches locally."
  echo
  echo "  Author mode is particularly useful when you are making content updates that span multiple repositories"
  echo "  or branches. It provides a local environment for documentation updates, making the process faster"
  echo "  and more efficient."
  echo
  echo "Arguments:"
  echo "  <repo_name>  The name of the repository (without the URL or organization prefix)."
  echo "               For example, 'docs' for 'https://github.com/$ORG/docs'."
  echo
  echo "Examples:"
  echo "  $0 docs cloud-docs"
  echo "    This will clone the 'docs' and 'cloud-docs' repositories from the"
  echo "    '$ORG' GitHub organization and set up their local worktrees."
  echo
  echo "Branches:"
  echo "  After cloning the repositories, you will be prompted to enter additional branches"
  echo "  you want to create as worktrees. You can enter multiple branches separated by spaces."
  echo "  If you don't specify any branches, only the default branch ($DEFAULT_BRANCH) will be set up."
  echo
  exit 1
}

# Check if at least one repository name is passed as an argument
if [ "$#" -lt 1 ]; then
  echo "Error: No repository names provided."
  show_help
fi

# Check if git is installed
if ! command -v git &> /dev/null; then
  echo "Error: git is not installed. Please install git and try again."
  exit 1
fi

# Create workspace folder if it doesn't exist
if [ ! -d "$WORKSPACE_DIR" ]; then
  echo "Creating workspace directory..."
  mkdir "$WORKSPACE_DIR" || { echo "Failed to create workspace directory"; exit 1; }
fi

# Loop through all provided repository names
for REPO_NAME in "$@"; do
  # Build the repository URL using the organization and repo name
  REPO_URL="https://github.com/$ORG/$REPO_NAME.git"

  # Create directory for the repository worktree
  REPO_DIR="$WORKSPACE_DIR/$REPO_NAME"

  # Clone the main branch if it hasn't been cloned yet
  MAIN_DIR="$REPO_DIR/$DEFAULT_BRANCH"
  if [ ! -d "$MAIN_DIR" ]; then
    echo "Cloning repository ($REPO_URL) into main worktree..."
    mkdir -p "$REPO_DIR" || { echo "Failed to create repository directory"; exit 1; }
    git clone "$REPO_URL" "$MAIN_DIR" || { echo "Failed to clone $REPO_URL"; exit 1; }
  else
    echo "Main repository for $REPO_NAME already exists."
  fi

  # Ask the user to provide branches they want to add to the worktree
  echo "Enter any additional branches you want to add for repository $REPO_NAME (separated by spaces), or press Enter to use only the default branch ($DEFAULT_BRANCH):"
  read -r BRANCHES

  # If no branches are provided, use the default branch
  if [ -z "$BRANCHES" ]; then
    BRANCHES="$DEFAULT_BRANCH"
  fi

  # Create linked worktrees for each branch provided by the user
  pushd "$MAIN_DIR" || { echo "Failed to enter directory $MAIN_DIR"; exit 1; }
  for BRANCH in $BRANCHES; do
    # Replace slashes (/) in branch names with hyphens (-) for folder names
    SANITIZED_BRANCH_NAME=$(echo "$BRANCH" | sed 's/\//-/g')

    WORKTREE_DIR="../$SANITIZED_BRANCH_NAME"
    if [ ! -d "$WORKTREE_DIR" ]; then
      echo "Creating worktree for branch $BRANCH (folder: $SANITIZED_BRANCH_NAME)..."
      git worktree add "$WORKTREE_DIR" "$BRANCH" || { echo "Failed to create worktree for branch $BRANCH"; exit 1; }
    else
      echo "Worktree for branch $BRANCH (folder: $SANITIZED_BRANCH_NAME) already exists."
    fi
  done

  # Return to the previous directory
  popd || exit

done

echo "Author Mode setup complete."
echo "You can now update your playbook to point to the local content."
echo
echo "Example configuration for your playbook:"
echo
echo "  - url: ./workspace/docs/main"
echo "    branches: [main, v/*]"
echo "    worktrees: true"
