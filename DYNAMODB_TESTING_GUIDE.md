# DynamoDB Testing Guide - Issue Resolution

## 🔴 Issues Found in Your Implementation

### Issue #1: Mock Environment Blocking DynamoDB ✅ FIXED

**Problem:** 
```python
if config.ENABLE_DYNAMODB and not config.IS_MOCK_ENVIRONMENT:
```

Since `IS_MOCK_ENVIRONMENT = True`, DynamoDB was **never initialized**.

**Fix Applied:** Removed the mock environment check to allow testing on laptop.

---

### Issue #2: Missing AWS Credentials ⚠️ ACTION REQUIRED

**Problem:** Docker container cannot access DynamoDB without AWS credentials.

**Solution:** Configure AWS credentials on your laptop.

---

## 🔧 Step-by-Step Fix

### Step 1: Configure AWS Credentials

1. **Get Your AWS Access Keys:**
   - AWS Console → IAM → Users → Your username
   - Security credentials tab
   - **Create access key** button
   - Select "Command Line Interface (CLI)"
   - Download/copy the credentials

2. **Edit the credentials file:**
   - Location: `C:\Users\harma\.aws\credentials`
   - Open in Notepad or VS Code
   - Replace with your actual keys:

   ```ini
   [default]
   aws_access_key_id = AKIAIOSFODNN7EXAMPLE
   aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
   ```

3. **Verify region in config file:**
   - Location: `C:\Users\harma\.aws\config`
   - Should contain:

   ```ini
   [default]
   region = ap-southeast-2
   output = json
   ```

---

### Step 2: Update Docker Compose to Pass Credentials

**Edit your `docker-compose.yml`:**

Find the `smart-hive-edge` service and add the volumes section:

```yaml
services:
  smart-hive-edge:
    build:
      context: .
      dockerfile: Dockerfile.edge
    container_name: smart-hive-edge
    environment:
      - AWS_ENDPOINT=${AWS_ENDPOINT}
      - CERT_FILE_NAME=${CERT_FILE_NAME}
      - KEY_FILE_NAME=${KEY_FILE_NAME}
      - S3_BUCKET_NAME=${S3_BUCKET_NAME}
      - SECRET_KEY=${SECRET_KEY}
    # ✨ ADD THIS SECTION:
    volumes:
      - ~/.aws:/root/.aws:ro  # Mount AWS credentials (read-only)
    networks:
      - smart-hive-net
    depends_on:
      - smart-hive-dashboard
```

**Why this works:**
- Docker mounts your local `~/.aws` folder into the container
- Boto3 automatically finds and uses these credentials
- `:ro` means read-only (security best practice)

---

### Step 3: Rebuild and Test

```powershell
# Stop containers
docker-compose down

# Rebuild with changes
docker-compose up --build
```

---

## ✅ What to Look For

### Success Indicators

**Terminal Output Should Show:**

```
Initializing Smart Hive System...
INITIALIZING MOCK ENVIRONMENT...
AWS clients initialized.
✅ DynamoDB table 'SmartHiveTelemetry' initialized successfully.
Successfully connected to AWS IoT Core.
Subscribed to control topic: hive/control
Starting all system threads...
All threads started. System is running.
```

**Every 5 seconds, you should see:**

```
Published Telemetry: {'timestamp': 1697123456, 'temperature': 34.5, 'humidity': 58.2, 'vibration_rms': 0.0521, 'sound_db': 52.3, 'sound_freq': 265.0}
✅ DynamoDB: Wrote record at 2025-10-14 15:30:45 (5 sensors)
```

---

### Failure Indicators

**❌ If you see:**

```
❌ Error initializing DynamoDB: Unable to locate credentials
```

**Fix:** AWS credentials not configured correctly. Re-check Step 1.

---

**❌ If you see:**

```
❌ Error initializing DynamoDB: An error occurred (ResourceNotFoundException)
```

**Fix:** Table doesn't exist or wrong region.
- Verify table name: `SmartHiveTelemetry` (exact spelling)
- Verify region in `config.py`: `AWS_REGION = "ap-southeast-2"`
- Check AWS Console that table exists in that region

---

**❌ If you see:**

```
❌ DynamoDB write error: An error occurred (AccessDeniedException)
```

**Fix:** IAM permissions missing.
- Check IAM policy includes `dynamodb:PutItem`
- For testing with AWS credentials, your IAM user needs DynamoDB permissions

---

**❌ If you see:**

```
⚠️  DynamoDB disabled (ENABLE_DYNAMODB = False)
```

**Fix:** Check `config.py` has `ENABLE_DYNAMODB = True`

---

## 🔍 Verify Data in AWS Console

### Method 1: DynamoDB Console

1. **Open AWS Console** → **DynamoDB**
2. **Click "Tables"** → **SmartHiveTelemetry**
3. **Click "Explore table items"**
4. **Click "Run"** button

You should see rows like:
```
device_id          timestamp      temperature  humidity  vibration_rms
SmartHive_Pi       1697123456     34.52        58.21     0.0521
SmartHive_Pi       1697123461     34.48        58.35     0.0518
```

### Method 2: PartiQL Query

1. **DynamoDB** → **PartiQL editor** (left sidebar)
2. Run this query:

```sql
SELECT * FROM SmartHiveTelemetry 
WHERE device_id = 'SmartHive_Pi'
ORDER BY timestamp DESC
LIMIT 10
```

---

## 🐛 Additional Troubleshooting

### Check Docker Logs in Real-Time

```powershell
# In a separate terminal, watch the edge container logs:
docker logs -f smart-hive-edge
```

Look for DynamoDB-related messages.

---

### Test AWS Credentials Manually

```powershell
# Install AWS CLI if not already installed:
# winget install Amazon.AWSCLI

# Test credentials:
aws sts get-caller-identity

# Should output:
# {
#     "UserId": "AIDAIOSFODNN7EXAMPLE",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/YourUsername"
# }

# Test DynamoDB access:
aws dynamodb describe-table --table-name SmartHiveTelemetry --region ap-southeast-2
```

If these commands fail, your credentials or permissions are incorrect.

---

### Check IAM User Permissions

Your IAM user needs this policy attached:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:DescribeTable"
      ],
      "Resource": "arn:aws:dynamodb:ap-southeast-2:*:table/SmartHiveTelemetry"
    }
  ]
}
```

**To attach:**
1. IAM → Users → Your user → Add permissions
2. Create inline policy → JSON tab → Paste above
3. Name: `DynamoDBSmartHiveAccess`
4. Create policy

---

## 📋 Complete Checklist

Before asking for help, verify:

### AWS Console
- [ ] DynamoDB table `SmartHiveTelemetry` exists
- [ ] Table is in region `ap-southeast-2`
- [ ] Table status is "Active"
- [ ] IAM user has DynamoDB permissions

### Local Configuration
- [ ] File exists: `C:\Users\harma\.aws\credentials`
- [ ] Contains valid AWS access key and secret
- [ ] File exists: `C:\Users\harma\.aws\config`
- [ ] Region set to `ap-southeast-2`

### Code Configuration
- [ ] `config.py` has `ENABLE_DYNAMODB = True`
- [ ] `config.py` has `AWS_REGION = "ap-southeast-2"`
- [ ] `config.py` has `DYNAMODB_TABLE = "SmartHiveTelemetry"`
- [ ] `app.py` has DynamoDB initialization (without mock check)
- [ ] `app.py` calls `write_to_dynamodb()` in telemetry loop

### Docker
- [ ] `docker-compose.yml` mounts `~/.aws` volume
- [ ] Containers rebuilt after changes: `docker-compose up --build`
- [ ] No error messages in startup logs

### Runtime
- [ ] Terminal shows: `✅ DynamoDB table 'SmartHiveTelemetry' initialized successfully.`
- [ ] Terminal shows: `✅ DynamoDB: Wrote record at ...` every 5 seconds
- [ ] AWS Console shows new records appearing

---

## 🎯 Quick Fix Summary

**The two main issues:**

1. ✅ **FIXED:** Removed mock environment check from DynamoDB initialization
2. ⚠️ **ACTION REQUIRED:** Configure AWS credentials in `~/.aws/credentials`

**After configuring credentials:**
```powershell
docker-compose down
docker-compose up --build
```

**Look for:**
- ✅ `DynamoDB table 'SmartHiveTelemetry' initialized successfully.`
- ✅ `DynamoDB: Wrote record at ...` messages every 5 seconds
- ✅ Data appearing in AWS Console

---

## 📞 Still Not Working?

Run these diagnostic commands and share the output:

```powershell
# 1. Check AWS credentials exist
Get-Content $env:USERPROFILE\.aws\credentials

# 2. Check AWS CLI can access DynamoDB
aws dynamodb describe-table --table-name SmartHiveTelemetry --region ap-southeast-2

# 3. Check Docker logs
docker logs smart-hive-edge 2>&1 | Select-String -Pattern "DynamoDB"

# 4. Check config values
docker exec smart-hive-edge python -c "import config; print(f'ENABLE_DYNAMODB={config.ENABLE_DYNAMODB}'); print(f'AWS_REGION={config.AWS_REGION}'); print(f'DYNAMODB_TABLE={config.DYNAMODB_TABLE}')"
```

Share the output of these commands for further troubleshooting.
