# Quick Start Guide

## For Laptop Development (5 minutes)

```bash
# 1. Clone and setup
git clone https://github.com/harmandeeppal/smart-hive-ai.git
cd smart-hive-ai
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Run tests (verify everything works)
pytest tests/ -v

# 3. Run application in mock mode
export IS_MOCK_ENVIRONMENT=true
python app.py

# 4. In another terminal, run dashboard
python dashboard/dashboard_app.py

# 5. In another terminal, run ML service
python ml_inference_service.py

# Open browser to http://localhost:5000
```

## For Raspberry Pi Deployment (10 minutes)

```bash
# 1. Prepare credentials
cp .env.example .env
nano .env  # Edit with your AWS IoT endpoint

# Copy AWS certificates
cp your_cert.pem certs/certificate.pem
cp your_key.pem certs/private.key
cp AmazonRootCA1.pem certs/

# 2. Deploy with Docker
docker-compose build
docker-compose up -d

# 3. Monitor
docker-compose logs -f

# 4. Verify MQTT
mosquitto_sub -h localhost -t "hive/#"
```

## Key Files

| Purpose | File | Run Command |
|---------|------|-------------|
| Tests | tests/test_all.py | `pytest tests/ -v` |
| Edge App | app.py | `python app.py` |
| ML Service | ml_inference_service.py | `python ml_inference_service.py` |
| Dashboard | dashboard/dashboard_app.py | `python dashboard/dashboard_app.py` |
| Configuration | config.py | (imported by other files) |

## Environment Variables (.env)

```bash
# AWS IoT Core
AWS_ENDPOINT=your-endpoint.iot.us-east-1.amazonaws.com
CERT_FILE_NAME=certificate.pem
KEY_FILE_NAME=private.key

# Flask
SECRET_KEY=your-secret-here

# Mock testing
IS_MOCK_ENVIRONMENT=true  # Set to false for production
```

## Testing

```bash
# All tests
pytest tests/ -v

# Specific test
pytest tests/test_all.py::TestMLModelsExist -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

## Troubleshooting

**Missing dependencies?**
```bash
pip install -r requirements.txt
```

**MQTT not working?**
- Check AWS_ENDPOINT in .env
- Verify certificates in certs/
- Ensure AWS IoT policy is correct

**Tests failing?**
```bash
# Check individual tests
pytest tests/test_all.py::TestConfiguration -v
```

## Documentation

- **Setup**: See `docs/SETUP_AND_DEPLOYMENT.md`
- **Deployment**: See `docs/DEPLOYMENT.md`
- **Configuration**: See `docs/CONFIGURATION_GUIDE.md`
- **Troubleshooting**: See `docs/TROUBLESHOOTING.md`
- **Cleanup Report**: See `PROJECT_CLEANUP_REPORT.md`

## Status

✅ All tests passing (20/21, 1 skipped)  
✅ Clean project structure  
✅ Production-ready  
✅ Docker configured  
✅ Documentation complete  

**Ready to deploy!**
