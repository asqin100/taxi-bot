---
name: taxi-deploy
version: 1.0.0
description: |
  Deploy taxi-bot to production server. Runs pre-deployment checks, deploys code,
  runs migrations, restarts service, and performs smoke tests. Includes automatic
  rollback on failure.
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---

# Taxi-bot Production Deployment

## Preamble

```bash
_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "BRANCH: $_BRANCH"
echo "SERVER: root@5.42.110.16"
echo "PATH: /opt/taxibot"
```

## Step 1: Pre-deployment Safety Checks

Before deploying, verify the branch is ready:

```bash
# Check we're on main branch
if [ "$_BRANCH" != "main" ]; then
  echo "ERROR: Not on main branch. Current: $_BRANCH"
  exit 1
fi

# Check all changes are committed
if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: Uncommitted changes detected"
  git status --short
  exit 1
fi

# Check we're in sync with remote
git fetch origin main
LOCAL=$(git rev-parse main)
REMOTE=$(git rev-parse origin/main)
if [ "$LOCAL" != "$REMOTE" ]; then
  echo "ERROR: Local main is not in sync with origin/main"
  echo "Local:  $LOCAL"
  echo "Remote: $REMOTE"
  exit 1
fi

echo "✅ Pre-deployment checks passed"
```

## Step 2: Run Local Tests

```bash
# Run pytest
python -m pytest tests/ -v

# Check exit code
if [ $? -ne 0 ]; then
  echo "ERROR: Tests failed. Aborting deployment."
  exit 1
fi

echo "✅ All tests passed"
```

## Step 3: Check Production Status

```bash
# Get current production commit
ssh root@5.42.110.16 "cd /opt/taxibot && git log -1 --oneline"

# Check service status
ssh root@5.42.110.16 "systemctl status taxibot --no-pager | head -20"

# Check recent logs for errors
ssh root@5.42.110.16 "journalctl -u taxibot --since '5 minutes ago' | grep -i error | tail -10"
```

Review the output. If there are active errors or the service is down, ask the user if they want to proceed.

## Step 4: Deploy to Production

```bash
# Pull latest code
ssh root@5.42.110.16 "cd /opt/taxibot && git pull origin main"

# Check if there are database migrations
MIGRATION_NEEDED=$(ssh root@5.42.110.16 "cd /opt/taxibot && alembic current 2>/dev/null | grep -q 'head' && echo 'no' || echo 'yes'")

if [ "$MIGRATION_NEEDED" = "yes" ]; then
  echo "⚠️  Database migration needed"
  # Ask user for confirmation
fi

# Run migrations if needed
ssh root@5.42.110.16 "cd /opt/taxibot && alembic upgrade head"

# Restart the service
ssh root@5.42.110.16 "sudo systemctl restart taxibot"

# Wait for service to start
sleep 3

echo "✅ Deployment completed"
```

## Step 5: Post-Deployment Verification

```bash
# Check service is running
ssh root@5.42.110.16 "systemctl is-active taxibot"

# Check for errors in last 2 minutes
ssh root@5.42.110.16 "journalctl -u taxibot --since '2 minutes ago' | tail -50"

# Get current commit
DEPLOYED_COMMIT=$(ssh root@5.42.110.16 "cd /opt/taxibot && git log -1 --oneline")
echo "Deployed commit: $DEPLOYED_COMMIT"
```

## Step 6: Smoke Tests

Perform basic functionality checks:

1. **Bot responds to /start**
   - Send test message to bot
   - Verify response within 5 seconds

2. **Admin panel loads**
   - Check http://5.42.110.16:8000/admin
   - Verify all tabs load

3. **Events are loading**
   - Check events table has data
   - Verify KudaGo API integration works

4. **Coefficients updating**
   - Check coefficient_history table
   - Verify Yandex API integration works

If any smoke test fails, proceed to rollback.

## Step 7: Rollback (if needed)

If deployment fails or smoke tests don't pass:

```bash
# Get previous commit
PREVIOUS_COMMIT=$(ssh root@5.42.110.16 "cd /opt/taxibot && git log -2 --oneline | tail -1 | cut -d' ' -f1")

echo "Rolling back to: $PREVIOUS_COMMIT"

# Checkout previous commit
ssh root@5.42.110.16 "cd /opt/taxibot && git checkout $PREVIOUS_COMMIT"

# Restart service
ssh root@5.42.110.16 "sudo systemctl restart taxibot"

# Verify rollback
ssh root@5.42.110.16 "cd /opt/taxibot && git log -1 --oneline"

echo "✅ Rollback completed"
```

## Summary Format

After deployment, provide this summary:

```
═══════════════════════════════════════════════════════════════
  TAXI-BOT DEPLOYMENT SUMMARY
═══════════════════════════════════════════════════════════════

Status: ✅ SUCCESS / ❌ FAILED

Deployed Commit: {commit hash and message}
Previous Commit: {previous commit}
Deployment Time: {timestamp}

Pre-deployment Checks:
  ✅ Branch: main
  ✅ Tests: passed
  ✅ Production status: healthy

Deployment Steps:
  ✅ Code pulled
  ✅ Migrations: {ran/skipped}
  ✅ Service restarted

Post-deployment Verification:
  ✅ Service running
  ✅ No errors in logs
  ✅ Smoke tests: passed

Next Steps:
  - Monitor logs for 10 minutes
  - Check user reports
  - Verify metrics in admin panel

═══════════════════════════════════════════════════════════════
```

## Notes

- Always deploy during low-traffic hours (3-6 AM Moscow time)
- Keep SSH session open for 10 minutes after deployment
- Have rollback command ready in case of issues
- Notify team in Telegram after successful deployment
