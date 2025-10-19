#!/bin/bash
# Camera Video Feed Diagnostics Script
# Run this on your Raspberry Pi to diagnose video feed issues

echo "==============================================="
echo "Smart Hive - Camera Video Feed Diagnostics"
echo "==============================================="
echo ""

echo "1. Checking if containers are running..."
echo "----------------------------------------"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "NAME|smart-hive-edge|smart-hive-dashboard"
echo ""

echo "2. Checking edge-app container name..."
echo "----------------------------------------"
EDGE_CONTAINER=$(docker ps --filter "name=edge" --format "{{.Names}}")
if [ -z "$EDGE_CONTAINER" ]; then
    echo "❌ Edge container NOT running!"
else
    echo "✅ Edge container: $EDGE_CONTAINER"
fi
echo ""

echo "3. Testing video feed endpoint from INSIDE dashboard container..."
echo "----------------------------------------"
docker exec smart-hive-dashboard curl -I http://smart-hive-edge:5001/video_feed 2>&1 | head -5
echo ""

echo "4. Alternative: Testing with 'edge-app' hostname..."
echo "----------------------------------------"
docker exec smart-hive-dashboard curl -I http://edge-app:5001/video_feed 2>&1 | head -5
echo ""

echo "5. Testing video feed from Raspberry Pi host..."
echo "----------------------------------------"
curl -I http://localhost:5001/video_feed 2>&1 | head -5
echo ""

echo "6. Checking dashboard logs for video errors..."
echo "----------------------------------------"
docker logs --tail 20 smart-hive-dashboard 2>&1 | grep -i "video\|error\|exception" || echo "No video-related errors in last 20 lines"
echo ""

echo "7. Checking edge-app logs for video stream..."
echo "----------------------------------------"
docker logs --tail 20 smart-hive-edge 2>&1 | grep -i "video\|camera\|5001" || echo "No video-related messages in last 20 lines"
echo ""

echo "8. Testing network connectivity between containers..."
echo "----------------------------------------"
echo "From dashboard to edge-app:"
docker exec smart-hive-dashboard ping -c 2 smart-hive-edge 2>&1 || echo "❌ Cannot reach smart-hive-edge"
echo ""

echo "9. Checking video_feed endpoint accessibility..."
echo "----------------------------------------"
echo "Attempting to fetch first frame (5 second timeout)..."
timeout 5 curl -s http://localhost:5001/video_feed --output /tmp/test_frame.jpg 2>&1
if [ -f /tmp/test_frame.jpg ]; then
    SIZE=$(stat -c%s /tmp/test_frame.jpg 2>/dev/null || stat -f%z /tmp/test_frame.jpg 2>/dev/null)
    echo "✅ Frame saved: /tmp/test_frame.jpg ($SIZE bytes)"
    rm /tmp/test_frame.jpg
else
    echo "❌ Failed to capture frame"
fi
echo ""

echo "10. Summary of potential issues..."
echo "----------------------------------------"
echo "Check the results above:"
echo "  - If 'edge-app' test fails but 'smart-hive-edge' works:"
echo "    → Dashboard is using wrong container name!"
echo "    → Fix: Update dashboard_app.py to use 'smart-hive-edge'"
echo ""
echo "  - If both container tests fail but localhost works:"
echo "    → Network issue between containers"
echo "    → Check docker-compose.yml networks"
echo ""
echo "  - If localhost test fails:"
echo "    → edge-app container not serving video"
echo "    → Check edge-app logs for errors"
echo ""
echo "==============================================="
echo "Diagnostic complete!"
echo "==============================================="
