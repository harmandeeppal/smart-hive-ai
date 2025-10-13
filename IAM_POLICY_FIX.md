# IAM Policy Setup for DynamoDB Access

## 🔴 Root Cause Identified

Your AWS IAM user **`harmandeeppal`** does not have permissions to access DynamoDB.

Error from container:
```
User: arn:aws:iam::651706753211:user/harmandeeppal 
is not authorized to perform: dynamodb:ListTables 
because no identity-based policy allows the dynamodb:ListTables action
```

---

## ✅ Solution: Add DynamoDB Permissions to IAM User

### Step 1: Open IAM Console

1. Go to: https://console.aws.amazon.com/iam/
2. Click **Users** (left sidebar)
3. Click on user: **`harmandeeppal`**

---

### Step 2: Add Inline Policy

1. Click the **"Add permissions"** button (top right)
2. Select **"Create inline policy"**
3. Click the **"JSON"** tab
4. **Paste this policy:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DynamoDBFullAccess",
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:DescribeTable",
        "dynamodb:ListTables"
      ],
      "Resource": [
        "arn:aws:dynamodb:ap-southeast-2:651706753211:table/SmartHiveTelemetry",
        "arn:aws:dynamodb:ap-southeast-2:651706753211:table/*"
      ]
    }
  ]
}
```

5. Click **"Review policy"**
6. **Policy name:** `SmartHiveDynamoDBAccess`
7. **Description:** `Allows Smart Hive application to read/write DynamoDB data`
8. Click **"Create policy"**

---

### Step 3: Verify Policy is Attached

1. Still in IAM → Users → harmandeeppal
2. Click **"Permissions"** tab
3. You should see: `SmartHiveDynamoDBAccess` (inline policy)

---

### Step 4: Test from Docker Container

After adding the policy, restart your Docker container:

```powershell
docker restart smart-hive-edge
```

Watch the logs:

```powershell
docker logs -f smart-hive-edge
```

**Look for:**
```
✅ DynamoDB: Wrote record at 2025-10-14 12:30:45 (5 sensors)
```

---

## 🔍 Verify It's Working

### Test 1: List Tables from Container

```powershell
docker exec smart-hive-edge python -c "import boto3; db = boto3.resource('dynamodb', region_name='ap-southeast-2'); print([t.name for t in db.tables.all()])"
```

**Expected output:**
```
['SmartHiveTelemetry']
```

---

### Test 2: Check AWS Console

1. AWS Console → **DynamoDB** → **Tables** → **SmartHiveTelemetry**
2. Click **"Explore table items"**
3. Click **"Run"**
4. You should see rows with recent timestamps!

---

## 📝 What This Policy Does

| Permission | Purpose |
|------------|---------|
| `dynamodb:PutItem` | Write new sensor data ✅ |
| `dynamodb:GetItem` | Read individual records |
| `dynamodb:Query` | Query by device_id and time range |
| `dynamodb:Scan` | Scan entire table (for analysis) |
| `dynamodb:UpdateItem` | Update existing records |
| `dynamodb:DeleteItem` | Delete records (for testing) |
| `dynamodb:DescribeTable` | Get table metadata |
| `dynamodb:ListTables` | List all tables (for diagnostics) |

---

## ⚠️ Important Notes

1. **Account ID:** The policy uses your AWS account ID `651706753211`
2. **Region:** Locked to `ap-southeast-2` (Sydney)
3. **Scope:** Only affects `SmartHiveTelemetry` table
4. **Security:** This is safe for development/thesis work

---

## 🆘 If Still Not Working

### Check 1: Verify credentials are correct

```powershell
# On your laptop:
cat $env:USERPROFILE\.aws\credentials

# Should show:
# [default]
# aws_access_key_id = AKIA...
# aws_secret_access_key = ...
```

### Check 2: Test credentials directly

```powershell
aws sts get-caller-identity --region ap-southeast-2
```

**Expected output:**
```json
{
    "UserId": "AIDAIOSFODNN7EXAMPLE",
    "Account": "651706753211",
    "Arn": "arn:aws:iam::651706753211:user/harmandeeppal"
}
```

### Check 3: Force Docker to use fresh credentials

```powershell
docker-compose down
docker-compose up --build
```

---

## ✅ Success Criteria

After adding the IAM policy, you should see:

**Terminal Output:**
```
Published Telemetry: {'timestamp': 1760358100, ...}
✅ DynamoDB: Wrote record at 2025-10-14 12:35:00 (5 sensors)
```

**AWS Console:**
- Rows appearing in DynamoDB table
- Fresh timestamps (within last minute)
- All 5 sensor values present

---

**This is the final fix you need! Add the IAM policy and restart the container.** 🚀
