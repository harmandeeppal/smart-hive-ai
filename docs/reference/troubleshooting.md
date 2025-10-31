# General Troubleshooting

Use this reference when you are unsure which subsystem is misbehaving. Detailed service guides live under `audio/guide.md` and `camera/guide.md`.

## Hardware
- **I2C sensors missing**
  ```bash
  sudo raspi-config   # enable I2C
  sudo i2cdetect -y 1
  ```
  Ensure the BME280 appears at `0x76/0x77` and the LIS3DH at `0x19/0x18`.
- **USB microphone or camera not detected**
  ```bash
  lsusb
  arecord -l
  ls -l /dev/video*
  ```
  Add the `pi` user to the `audio` and `video` groups and reboot if devices are missing.

## Docker
- **Container stuck restarting**
  ```bash
  docker compose ps
  docker logs <container-name>
  ```
  Look for missing environment variables or bad configuration paths.
- **Permission denied on `/dev/*` devices** – confirm the `devices:` mapping exists in `docker-compose.yml` and the user is in the correct group.

## MQTT Connectivity
- Check broker reachability from inside containers:
  ```bash
  docker exec -it smart-hive-edge sh -c "mosquitto_pub -h mosquitto -t test -m ping"
  docker exec -it smart-hive-edge sh -c "mosquitto_sub -h mosquitto -t test -C 1"
  ```
- Use `mosquitto_sub -h localhost -t 'hive/#' -v` on the host to inspect live traffic.

## AWS Integrations (optional)
- DynamoDB writes failing? Ensure `ENABLE_DYNAMODB` is `True` and AWS credentials exist in `.env`.
- Test AWS CLI connectivity:
  ```bash
  aws sts get-caller-identity --profile smart-hive
  ```
- Remember that S3 uploads are disabled by default; remove the feature flag only if the code path has been re-enabled.

## Video Feed
- Run through `camera/troubleshooting.md`.
- Verify the dashboard proxy points to `smart-hive-edge` and the camera service logs `Camera initialized successfully`.

## Audio ML
- See `audio/guide.md` for device checks, logging tips, and confidence tuning advice.
- Remember to rebuild the audio container whenever the model or configuration changes.

## When to Collect Logs
- Capture `docker compose logs -f` output during reproductions.
- Save exact MQTT payloads when investigating classification discrepancies.
- Note any `InconsistentVersionWarning` messages; they can usually be ignored unless inference fails.

Escalate with full logs, hardware specs, and configuration values to reduce back-and-forth when requesting support.
