# This script automates adding, committing, and pushing changes to GitHub.

# 1. Check if a commit message was provided as an argument.
if ($args.Count -eq 0) {
    # If no message is provided, show an error and exit.
    Write-Host "Error: Please provide a commit message."
    Write-Host "Example: .\upload.ps1 'Add new feature'"
    exit 1
}

# 2. Get the commit message from the first argument.
$commitMessage = $args[0]

# 3. Add all changed files to the staging area.
Write-Host "==> Adding all files..."
git add .

# 4. Commit the changes with the provided message.
Write-Host "==> Committing changes with message: '$commitMessage'..."
git commit -m "$commitMessage"

# 5. Push the changes to the 'main' branch on GitHub.
Write-Host "==> Pushing to GitHub..."
git push origin main

Write-Host "==> Done!"
