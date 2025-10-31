# Documentation Index

Use this index to navigate the Smart Hive AI documentation set. The layout mirrors the current container stack (edge, audio, optional vision, dashboard, Mosquitto) as of October 2025.

## Start Here
1. **Overview** – read `../README.md` for hardware requirements, service topology, and deployment prerequisites.
2. **Quick start** – follow `core/quick-start.md` for a sequential Raspberry Pi setup checklist.
3. **Full deployment** – consult `core/deployment.md` when provisioning a new device end to end (OS preparation, Docker install, verification).
4. **Container builds** – see `core/build-containers.md` for detailed image build procedures and advanced troubleshooting.

## Operational Guides
- **Audio ML** – configuration, pipeline internals, dashboard behaviour, and troubleshooting in `audio/guide.md`.
- **Camera stream** – configuration, diagnostics, and common fixes in `camera/guide.md`.
- **Reference material** – cross-cutting configuration and generic troubleshooting in `reference/configuration-guide.md` and `reference/troubleshooting.md`.

## Troubleshooting Shortcuts
- Audio-specific issues: jump to `audio/guide.md#troubleshooting-checklist`.
- Camera issues: see `camera/guide.md#common-remedies`.
- General Raspberry Pi / Docker faults: `reference/troubleshooting.md`.

## Optional / Advanced Components
- Vision service: deploy `ml_vision_service.py` with a trained `models/vision_model.pt` model and the `smart-hive-vision` container. Disable the service in `docker-compose.yml` and `config.py` if not required.
- DynamoDB logging: enable via `.env` and `config.py` feature flags only when the AWS infrastructure is in place.

## Maintenance Notes
- Update documentation alongside feature changes to keep this index accurate.
- When retiring a component, remove its references here and archive supporting documents outside the repository.

For support, raise issues in the project tracker or reach out to the maintainers with relevant log excerpts and configuration details.
