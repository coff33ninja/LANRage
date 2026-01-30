# GitHub Release Workflow Setup Guide

## Overview

This guide explains how to configure the GitHub release workflow to successfully create releases. The workflow may encounter 403 errors due to permission restrictions with the default `GITHUB_TOKEN`.

## Current Configuration

The workflow currently uses the default `GITHUB_TOKEN` with expanded permissions:
- `contents: write` - Required for creating releases
- `discussions: write` - Optional, for release discussions
- `pull-requests: write` - Additional permission for better compatibility

## If You Encounter 403 Errors

If the release workflow fails with a 403 error despite the permissions configuration, you'll need to use a Personal Access Token (PAT).

### Step 1: Create a Personal Access Token

1. Go to GitHub Settings: https://github.com/settings/tokens
2. Click **"Developer settings"** in the left sidebar
3. Click **"Personal access tokens"** → **"Tokens (classic)"**
4. Click **"Generate new token"** → **"Generate new token (classic)"**
5. Configure the token:
   - **Note**: `LANrage Release Workflow`
   - **Expiration**: Choose your preferred expiration (90 days, 1 year, or no expiration)
   - **Scopes**: Check the following:
     - ✅ `repo` (Full control of private repositories)
       - This includes: `repo:status`, `repo_deployment`, `public_repo`, `repo:invite`, `security_events`
6. Click **"Generate token"**
7. **IMPORTANT**: Copy the token immediately - you won't be able to see it again!

### Step 2: Add Token to Repository Secrets

1. Go to your repository: https://github.com/coff33ninja/LANRage
2. Click **"Settings"** tab
3. In the left sidebar, click **"Secrets and variables"** → **"Actions"**
4. Click **"New repository secret"**
5. Configure the secret:
   - **Name**: `GH_PAT`
   - **Secret**: Paste the token you copied in Step 1
6. Click **"Add secret"**

### Step 3: Update the Workflow

Edit `.github/workflows/release.yml` and change line 36:

**Before:**
```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**After:**
```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GH_PAT }}
```

Also update line 67 (Upload release assets step):

**Before:**
```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**After:**
```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GH_PAT }}
```

### Step 4: Commit and Push

```bash
git add .github/workflows/release.yml
git commit -m "chore: Switch to PAT for release workflow"
git push origin main
```

### Step 5: Test the Release Workflow

Create and push a test tag:

```bash
git tag v1.1.0-test
git push origin v1.1.0-test
```

Check the Actions tab to verify the release was created successfully.

## Troubleshooting

### 403 Error Persists

If you still get 403 errors after using a PAT:

1. **Verify token scope**: Make sure the PAT has `repo` scope
2. **Check token expiration**: Ensure the token hasn't expired
3. **Verify secret name**: Confirm the secret is named exactly `GH_PAT`
4. **Check repository settings**: Ensure Actions have permission to create releases:
   - Go to Settings → Actions → General
   - Under "Workflow permissions", select "Read and write permissions"
   - Check "Allow GitHub Actions to create and approve pull requests"

### Token Expired

If your PAT expires:

1. Generate a new token following Step 1
2. Update the `GH_PAT` secret in repository settings (Step 2)
3. No code changes needed - the workflow will automatically use the new token

### Alternative: Fine-grained Personal Access Token

GitHub now offers fine-grained tokens with more specific permissions:

1. Go to https://github.com/settings/tokens?type=beta
2. Click **"Generate new token"**
3. Configure:
   - **Token name**: `LANrage Release Workflow`
   - **Expiration**: Choose your preference
   - **Repository access**: Select "Only select repositories" → Choose `LANRage`
   - **Permissions**:
     - Repository permissions:
       - ✅ Contents: Read and write
       - ✅ Metadata: Read-only (automatically selected)
4. Generate and add to secrets as `GH_PAT`

## Security Best Practices

1. **Use fine-grained tokens** when possible for better security
2. **Set expiration dates** on tokens (90 days or 1 year recommended)
3. **Rotate tokens regularly** before they expire
4. **Never commit tokens** to the repository
5. **Use repository secrets** for storing tokens
6. **Limit token scope** to only what's needed (just `repo` for releases)

## Why This Is Needed

GitHub Actions' default `GITHUB_TOKEN` has restricted permissions for security reasons. While we've configured the workflow with explicit permissions, some repository settings or organization policies may still restrict the token's ability to create releases. Using a PAT bypasses these restrictions by using your personal GitHub account's permissions.

## References

- [GitHub Actions Permissions](https://docs.github.com/en/actions/security-guides/automatic-token-authentication#permissions-for-the-github_token)
- [Creating a Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [softprops/action-gh-release Documentation](https://github.com/softprops/action-gh-release)
