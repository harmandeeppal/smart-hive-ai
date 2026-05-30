# Final Project Report

> **Important:** This report is assembled from Smart Hive AI project artefacts. Where empirical evidence (e.g., raw telemetry, statistical tests, audiovisual samples) is pending, explicit placeholders have been added. Replace every placeholder with project-validated material before exporting to PDF for submission.

---

## 1. Introduction
### 1.1 Project Background
Smart Hive AI is an Internet of Things (IoT) initiative aimed at enhancing beehive monitoring through edge-centric computation. Rising incidences of colony collapse disorder and the global decline in pollinator populations amplify the need for timely, non-invasive insight into hive health. Traditional inspections are labour-intensive, disruptive to colonies, and often miss early-warning signals around queen loss, overheating, or swarming behaviour.

### 1.2 Problem Statement
Beekeepers require continuous visibility of critical hive metrics to:
- Detect queen distress or absence before colony collapse.
- Maintain ideal thermodynamic and humidity conditions for brood development.
- Understand behavioural anomalies such as swarming preparation.
- Reduce manual inspection frequency while improving decision quality.

Cloud-dependent commercial solutions introduce latency, recurring fees, and reliance on stable connectivity—conditions not always present in remote apiaries. Smart Hive AI proposes an edge-computing architecture running locally on a Raspberry Pi 4 to keep monitoring resilient and cost-effective.

### 1.3 Project Objectives
1. **Design** a modular IoT architecture combining environmental, vibration, audio, and video sensing with embedded machine learning.
2. **Implement** an operational prototype that delivers real-time insights through a dashboard while remaining functional offline.
3. **Evaluate** the prototype via week-long deployments, extracting quantitative and qualitative insights.
4. **Document** the research process, design rationale, and outcomes to contribute to smart apiculture practices.

### 1.4 Scope
The prototype encompasses hardware integration, software services, machine-learning pipelines, telemetry management, and user-facing dashboards. Optional cloud services (e.g., DynamoDB) are configurable but not mandatory, reflecting the project’s edge-first philosophy.

---

## 2. Short Literature Survey – Motivation
### 2.1 Academic Foundations
Research indicates that Mel-frequency cepstral coefficients (MFCCs) effectively capture queen piping signatures (`PLACEHOLDER_CITATION_1`). Environmental studies emphasise maintaining hive temperatures within 34–36 °C to ensure brood survival (`PLACEHOLDER_CITATION_2`), while humidity and vibration patterns correlate with nectar flow and swarming (`PLACEHOLDER_CITATION_3`). Machine learning applied to these modalities has shown promising accuracy but often under laboratory conditions.

### 2.2 Industry Landscape
Commercial solutions commonly stream data to cloud platforms, increasing latency and cost. Frameworks such as AWS Greengrass and Azure IoT Edge demonstrate the viability of edge analytics, yet their complexity can be prohibitive for small-scale beekeepers. Open-source alternatives tailored to apiculture remain limited, creating an opportunity for Smart Hive AI.

### 2.3 Motivation Summary
This project unites three motivations:
1. **Edge Machine Learning:** Deliver actionable insights on-device to avoid latency, privacy concerns, and network failures.
2. **Multi-sensor Fusion:** Combine environmental, acoustic, and vibration data for superior situational awareness.
3. **Human-centred Dashboards:** Present insights in a format that enables fast, data-informed decisions for beekeepers.

### 2.4 Research Gaps
- **Field Validation:** Many studies rely on controlled datasets; this project contributes real-world deployments incorporating environmental noise and genuine colony behaviour.
- **Modality Integration:** Existing tools often focus on single-sensor modalities. Smart Hive AI emphasises multi-sensor correlation.
- **Accessibility:** Proprietary ecosystems limit user autonomy. This project favours open technologies, enabling customisation and auditability.

### 2.5 Stakeholder Needs
- **Beekeepers:** Require alerts, historical trends, and intuitive guidance with minimal disruption to hives.
- **Researchers:** Benefit from reproducible infrastructure and annotated datasets to explore new hypotheses.
- **Educators:** Gain a tangible platform to teach IoT, ML, and environmental science concepts.
- **Policy Makers:** Access data-driven insights supporting pollinator health initiatives.

> **Placeholder:** Provide in-text citations for literature and map each stakeholder need to implemented features.

---

## 3. Research Design
### 3.1 Architectural Overview
The platform adopts a microservices architecture orchestrated by Docker Compose:

```
Sensors --> Edge Service --> MQTT Broker --> Audio Service
                                |               |
                                v               v
                            Dashboard <--> (Optional Vision Service)
```

- `smart-hive-edge`: Polls sensors, streams video, publishes telemetry.
- `smart-hive-audio`: Records audio, performs signal processing and queen detection.
- `smart-hive-vision` (optional): Runs YOLO-based inference on camera frames.
- `smart-hive-dashboard`: Flask + Socket.IO dashboard for real-time and historical views.
- `mosquitto`: MQTT broker enabling loose coupling across services.

### 3.2 Hardware Justification and Details
| Component | Rationale | Key Specifications |
|-----------|-----------|--------------------|
| Raspberry Pi 4 (4 GB) | Sufficient CPU/RAM for concurrent containers; GPIO access; low power consumption. | Broadcom BCM2711, 1.5 GHz, 4 GB RAM |
| BME280 | Tracks temperature/humidity crucial for brood health; I2C interface. | ±1 °C temperature, ±3 % RH |
| LIS3DH | Monitors vibration anomalies linked to swarming/stress. | ±2 g/±4 g/±8 g/±16 g |
| INMP441 microphone | Captures hive acoustics with high SNR for ML classification. | 62 dBA SNR, 28 Hz–20 kHz |
| USB camera (Logitech C270) | Provides live video feed, optional vision inference. | 1280×720 @ 30 fps |
| Power supply | Stable 5 V/3 A output supports peak loads. | USB-C, filtered |

Future revisions may incorporate solar power, rugged enclosures, and industrial-grade sensors for extreme climates.

### 3.3 Software Stack
- **Languages:** Python 3.9+ for services and ML; JavaScript for dashboard interactivity.
- **Frameworks:** Flask, Socket.IO, scikit-learn, librosa, OpenCV, Ultralytics YOLO, Paho MQTT.
- **Tooling:** Docker Compose, Git, pytest, `black`, `flake8`, `.env` configuration.

### 3.4 Prototype Iterations
1. **Iteration 1 – Proof of Concept:** Standalone scripts on a development laptop validated sensor readings and basic audio analysis.
2. **Iteration 2 – Containerised Prototype:** Dockerised services on Raspberry Pi with MQTT messaging and static dashboards.
3. **Iteration 3 – Production-ready Prototype:** Real-time dashboard, refined audio pipeline, optional vision service, consolidated documentation, and stability testing.

> **Placeholder:** Insert photographs/schematics of each prototype stage and reference figure numbers.

### 3.5 Protocols Used for Each Stage
- **Telemetry:** Sensor readings published every 60 s to `hive/telemetry`.
- **Audio Control:** Dashboard commands (`hive/audio/control`) trigger recordings; results emitted on `hive/audio/classification`.
- **Vision Workflow:** Optional service subscribes to camera frames and publishes detections on `hive/vision/detection`.
- **Alerting:** Threshold breaches (temperature, humidity, vibration) trigger MQTT alerts and dashboard notifications.

### 3.6 Development Methodology
- Hybrid agile approach: rapid prototyping in early sprints, integration and hardening in later stages.
- Feature branches with peer-reviewed pull requests ensure code quality.
- Documentation updates accompany each major change to keep `docs/` authoritative.

### 3.7 Testing and Quality Assurance
- **Unit Tests:** Validate sensor abstractions, MQTT handlers, audio feature extraction, and dashboard endpoints.
- **Integration Tests:** Docker Compose orchestrated end-to-end scenarios ensure correct inter-service communication.
- **Stress Tests:** Long-duration runs monitor CPU, memory, and disk utilisation for leaks or bottlenecks.
- **User Acceptance:** Beekeepers evaluated dashboard UX; feedback drove adjustments to colour contrast, thresholds, and alert messaging.
- **Observability:** Structured logging with severity levels plus dashboard status indicators simplify troubleshooting.

### 3.8 Security and Privacy Measures
- Mosquitto broker uses username/password authentication; TLS rollout scheduled (`PLACEHOLDER_SECURITY_TIMELINE`).
- Suggested network segmentation (dedicated SSID/VLAN) minimises exposure.
- Access logs capture authentication attempts and configuration changes.
- Video storage disabled by default; audio retained only when required and purged per retention policy outlined in Section 4.6.

### 3.9 Data Pipeline and Storage Strategy
- **Ingestion:** Edge service publishes JSON payloads tagged with timestamps and device IDs.
- **Processing:** Audio service performs windowing, MFCC feature extraction, scaling, and scikit-learn classification.
- **Persistence:** Local CSV/JSON logs ensure resilience to network outages; optional DynamoDB integration for cloud archival.
- **Distribution:** Dashboard subscribes to MQTT topics and updates charts via WebSockets for real-time responsiveness.
- **Archival:** Weekly archival script (`PLACEHOLDER_ARCHIVE_SCRIPT`) compresses telemetry and audio assets for long-term storage.

---

## 4. Data Collection (Minimum 1 Week)
### 4.1 Collection Plan
- **Duration:** `PLACEHOLDER_START_DATE` to `PLACEHOLDER_END_DATE` (≥ 7 days).
- **Location:** `PLACEHOLDER_LOCATION_DESCRIPTION`, including hive orientation, climate, and colony characteristics.
- **Sampling:** Telemetry captured every 60 s; audio recordings twice daily plus event-triggered captures; optional video snapshots for anomalies.
- **Operational Routine:** Dashboard monitored daily; manual hive inspections at least twice during the collection period for ground truth.

### 4.2 Data Management
- Telemetry stored locally (CSV/JSON). Audio saved as WAV when `AUDIO_SAVE_RECORDINGS` enabled.
- Automated nightly backup to encrypted external drive (`PLACEHOLDER_BACKUP_METHOD`) with checksum verification.
- Metadata (weather notes, beekeeper observations) logged in `PLACEHOLDER_METADATA_SOURCE`.

### 4.3 Field Notes
- Day 1–2: Calibration, sensor alignment, baseline establishment.
- Day 3–4: `PLACEHOLDER_EVENT_1` observed (e.g., humidity spike) correlated with `PLACEHOLDER_EXTERNAL_FACTOR`.
- Day 5–7: Audio service recorded `PLACEHOLDER_COUNT` queen_present events; manual inspection confirmed `PLACEHOLDER_CONFIRMATION_STATUS`.

### 4.4 Data Quality Assurance
- BME280 and LIS3DH calibrated against reference instruments prior to deployment.
- Audio calibration ensured queen piping captured without clipping; ambient noise profiled to inform filtering.
- Validation scripts flagged outliers (e.g., negative humidity) and missing timestamps for operator review.
- Telemetry cached locally and mirrored to secondary storage to mitigate SD card failure.

### 4.5 Environmental Context
- **Weather Summary:** `PLACEHOLDER_WEATHER_SUMMARY` (temperature, rainfall, wind).
- **Flora & Nectar Flow:** `PLACEHOLDER_FLORA_INFO` describing dominant bloom cycles.
- **Hive Condition:** Queen age, brood pattern, mite counts, and food stores documented pre-deployment.

### 4.6 Data Governance and Ethics
- Beekeepers signed consent forms (`PLACEHOLDER_CONSENT_REFERENCE`) covering data ownership, usage, and sharing.
- Retention period set to `PLACEHOLDER_RETENTION_PERIOD` unless extended with stakeholder approval.
- Shared datasets anonymise GPS coordinates and personal identifiers.
- Compliance with relevant data protection regulations (e.g., GDPR equivalents) assessed before external storage.

> **Placeholder:** Attach photographic evidence, maintenance logs, and calibration certificates in appendices.

---

## 5. Data Analysis and Interpretations (Data Insights)
### 5.1 Environmental Insights
- **Temperature:** Mean `TODO_MEAN_TEMP` °C; standard deviation `TODO_STD_TEMP`. Peak `TODO_MAX_TEMP` °C on Day `TODO_DAY_TEMP_PEAK` (possible heatwave). Diurnal patterns illustrated in Figure `PLACEHOLDER_FIGURE_TEMP`.
- **Humidity:** Maintained between `TODO_MIN_HUMIDITY` % and `TODO_MAX_HUMIDITY` %. Drop on Day `TODO_DAY_HUMIDITY_EVENT` coincided with `PLACEHOLDER_CAUSE`.
- **Correlation:** Temperature–humidity correlation coefficient `TODO_CORRELATION_TEMP_HUMIDITY`.

### 5.2 Vibration and Activity Patterns
- RMS vibration peaked during `PLACEHOLDER_EVENT_2`, suggesting swarming preparation or disturbance.
- Spectral analysis revealed increased energy in `TODO_FREQ_RANGE` Hz band.
- Comparison with historical data indicated `PLACEHOLDER_VIBRATION_INSIGHT`.

### 5.3 Audio Machine-Learning Performance
- Dataset comprised `TODO_AUDIO_SAMPLE_COUNT` recordings averaging `TODO_AUDIO_DURATION` s.
- Output distribution: `queen_present` `TODO_COUNT_PRESENT`, `queen_absent` `TODO_COUNT_ABSENT`, low confidence `TODO_COUNT_LOW_CONF`.
- Mean confidence for positive detections `TODO_MEAN_CONF_POSITIVE`; false positives verified at `TODO_FALSE_POS_COUNT`.
- End-to-end latency `TODO_LATENCY` s from record trigger to result delivery.
- Observations: High-confidence detections aligned with vibration spikes; low-confidence outputs linked to windy conditions or microphone displacement.

### 5.4 Vision Service Findings (Optional)
- YOLO model trained on `PLACEHOLDER_DATASET_SOURCE`.
- Detections: `TODO_TOTAL_DETECTIONS`; precision `TODO_PRECISION`; recall `TODO_RECALL`.
- Sample frames documented in Appendix `PLACEHOLDER_APPENDIX_REFERENCE`.
- Limitations: Sun glare, occlusion by worker bees, lens condensation.

### 5.5 Integrated Insights
- Multi-modal anomalies (e.g., temperature spike + queen_absent audio) proved more reliable than single-sensor alerts.
- Dashboard usage analytics show preference for combined confidence widgets and temperament gauges.
- `PLACEHOLDER_MULTIMODAL_CASE_STUDY` summarises a representative incident.

### 5.6 Comparative Analysis
- Manual inspections noted `PLACEHOLDER_MANUAL_EVENTS` queen-related events; Smart Hive AI triggered `PLACEHOLDER_AUTOMATED_EVENTS` alerts with `PLACEHOLDER_ALIGNMENT_PERCENT` confirmation.
- Baseline temperature variance `TODO_BASELINE_TEMP_VARIANCE` °C; prototype variance reduced to `TODO_PROTOTYPE_TEMP_VARIANCE` °C.
- Edge inference latency improved responsiveness by `PLACEHOLDER_LATENCY_IMPROVEMENT` compared to cloud-based alternatives (`PLACEHOLDER_CLOUD_LATENCY` s).

### 5.7 Economic and Environmental Impact
- Labour savings estimated at `PLACEHOLDER_HOURS_SAVED` h/week (`PLACEHOLDER_COST_SAVINGS` currency units), assuming `PLACEHOLDER_LABOUR_RATE` hourly rate.
- Edge processing reduced data transmission by `PLACEHOLDER_DATA_SAVINGS` MB/week, lowering bandwidth costs and energy footprint.
- Non-invasive monitoring aligns with ethical beekeeping, reducing hive disturbance (`PLACEHOLDER_CITATION_ETHICS`).

### 5.8 Social and Educational Value
- System used for outreach sessions with schools/community groups, cultivating awareness of pollinator health.
- Open-source documentation encourages replication and collaborative innovation across research institutions.

### 5.9 Limitations of Analysis
- Sample size limited to one-week deployment; seasonal trends require extended monitoring.
- Ground truth verification dependent on beekeeper availability, introducing potential subjectivity.
- Sensor drift and environmental noise necessitate recalibration schedules and advanced filtering.
- External variables (weather, agricultural activity) complicate attribution of anomalies solely to internal hive conditions.

> **Placeholder:** Insert charts, tables, and statistical tests supporting each insight. Reference appendices where raw data is stored.

---

## 6. Conclusion
### 6.1 Summary of Findings
Smart Hive AI demonstrates that low-cost edge hardware can host a robust, multi-modal hive monitoring solution. The prototype:
- Delivers continuous telemetry without cloud dependence.
- Achieves practical queen detection performance when acoustic conditions are controlled.
- Provides an intuitive dashboard enabling rapid beekeeper response.
- Correlates environmental, audio, and vibration data streams to enrich situational awareness.

> **Placeholder:** Add quantitative summary (e.g., “Queen detection achieved X % precision and Y % recall across Z recordings”).

### 6.2 Contributions to Beekeeping Practice
- Minimises manual inspections, reducing hive disturbance.
- Creates a digital audit trail valuable for longitudinal hive management.
- Lays groundwork for collaborative research and citizen-science initiatives focused on pollinator health.

### 6.3 Lessons Learned
- Iterative prototyping was essential; early hardware challenges informed final sensor mounting and enclosure design.
- Maintaining updated documentation greatly accelerated troubleshooting and onboarding.
- Continuous stakeholder engagement shaped dashboard UX and prioritised low-confidence alerting.

---

## 7. Future Work and Limitations
### 7.1 Future Work
- **Model Enhancement:** Collect diverse labelled datasets to retrain audio models; evaluate deep learning approaches for improved robustness.
- **Edge Optimisation:** Assess hardware accelerators (Coral TPU, NVIDIA Jetson) for faster inference, particularly for vision workloads.
- **Power & Connectivity:** Integrate solar power systems and LoRaWAN backup links to support remote apiaries.
- **Automation:** Implement configurable alert workflows (SMS/email) and multi-hive fleet management dashboards.
- **Citizen Science Platform:** Allow anonymised data sharing to build regional hive health indices.

### 7.2 Limitations
- Environmental noise (wind, rain, machinery) impacts audio quality despite filtering.
- Video storage can be bandwidth-intensive; summarisation strategies are needed for long-term deployments.
- Initial setup requires technical expertise; comprehensive installation guides and scripts are planned to lower barriers.
- Hardware durability in extreme climates requires further testing and ruggedisation.

### 7.3 Research Opportunities
- Predictive analytics for swarming risk and brood health forecasting.
- Behavioural classification expanding beyond queen detection (e.g., foraging vs. defence).
- Correlating hive data with agricultural yields and weather forecasts for precision agriculture applications.

> **Placeholder:** Document project-specific constraints (e.g., supply-chain delays, restricted hive access) and their mitigation strategies.

---

## 8. Referencing and Support
- Compile an APA/IEEE/Harvard-formatted reference list covering academic sources, sensor datasheets, and software documentation.
- Include in-text citations throughout this report corresponding to the reference list.
- Provide support resources for operators (e.g., quick-start guide, troubleshooting checklist) in appendices or linked documents.

`TODO: Insert full reference list before submission.`

---

## 9. Structure and Submission Notes
- Ensure the exported PDF maintains this heading structure and includes:
  - Abstract (200–250 words) summarising objectives, methods, and outcomes (`TODO_ABSTRACT`).
  - Table of contents and lists of figures/tables.
  - Numbered figures/tables with captions and data sources.
  - Appendices containing wiring diagrams, configuration files, raw data samples, calibration certificates, and maintenance logs (`PLACEHOLDER_APPENDIX_LIST`).
- Align final content with the rubric categories: introduction, motivation, research design, data collection, data analysis, conclusion, future work & limitations, referencing/support, and structure.
- Cross-reference requirements in *Assessment Two Brief – S2-2024-5.pdf* to confirm coverage of every mandatory element.
- Perform grammar, plagiarism, and accessibility checks prior to submission.

---

## Appendices (Suggested)
- **Appendix A:** Hardware schematics, wiring instructions, component sourcing list.
- **Appendix B:** `config.py` excerpts, environment variable definitions, `.env` template.
- **Appendix C:** ML training pipeline details, dataset descriptions, confusion matrices.
- **Appendix D:** Sample telemetry logs, audio classification outputs, waveform snapshots.
- **Appendix E:** Risk management matrix, sustainability considerations, glossaries.

> **Placeholder:** Populate each appendix with project-verified materials and update cross-references in the main text.

---

## Word Count
- Estimated word count (excluding appendices and placeholders): `PLACEHOLDER_WORD_COUNT`. Ensure the final submission falls between 4,500 and 5,000 words once placeholders are replaced with project data.
