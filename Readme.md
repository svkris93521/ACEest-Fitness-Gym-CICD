# DevOps CI/CD Implementation Report
**Project:** ACEest Fitness & Gym
**Assignment Type:** DevOps CI/CD Implementation

## 1. CI/CD Architecture Overview

The automated end-to-end continuous integration and continuous delivery pipeline for ACEest Fitness & Gym was established using a combination of industry-standard DevOps tools to provide scalability, testing capabilities, and robust deployment strategies. 

**Application Refactoring**: The original Tkinter-based thick-client application was decoupled and migrated to a lightweight **Flask Web Application**, allowing it to be containerized and run cleanly in the cloud/Kubernetes without GUI thread blocks. This serves the core RESTful APIs.

**Version Control System (Git & GitHub)**: Source code is maintained incrementally via structured branching, committing, and tagging, which serves as the foundational trigger for the CI pipeline.

**Continuous Integration (Jenkins & Pytest & SonarQube)**:
A declarative `Jenkinsfile` controls the CI workflow:
1. **Source Checkout**: Code is pulled securely upon Git commit triggers.
2. **Automated Testing**: `pytest` executes unit test suites ensuring changes don't fracture the API architecture. Test execution yields XML reports integrated into the Jenkins dashboard.
3. **Static Code Analysis**: SonarQube runs locally to enforce the Quality Gate strictly, failing the build on critical bugs, code smells, or severe technical debt.
4. **Containerization Engine (Docker)**: Successful builds result in packaging the Flask logic, `gunicorn` ASGI server, and dependencies into a lightweight python `slim` image. This guarantees parity across dev, staging, and production. The finalized manifest is pushed to Docker Hub with timestamped build tags.

**Continuous Delivery (Kubernetes)**:
Kubernetes (`minikube`) acts as the orchestration layer targeting advanced deployment strategies:
- **Rolling Updates**: The CI pipeline inherently replaces pods iteratively using the native `kubectl apply -f k8s/deployment.yaml` rollout methodology, enabling zero downtime.
- **Blue-Green Deployment (`k8s/blue-green.yaml`)**: An identical secondary cluster environment receives the new version, allowing safe pre-launch validation. Traffic routing flips simply by shifting the underlying service `selector` label.
- **Canary Release (`k8s/canary.yaml`)**: Incremental fraction scaling directs ~10-25% of load to testing replicas to cautiously monitor real-world latency and success rates.

## 2. Challenges Faced & Mitigation Strategies

- **Challenge:** Containerizing a localized `Tkinter` Application.
  - **Mitigation:** The application inherently assumed a desktop GUI topology. Taking the DevOps approach, the core logic (sqlite3 database handler, metrics structure) was ported successfully to a Flask application that returns HTML templates and JSON data instead.
  
- **Challenge:** Managing Local Environments & Toolchain.
  - **Mitigation:** Because environments like macOS lack intrinsic Minikube instances pre-installed sometimes, Kubernetes manifestations were strictly abstracted into standard parameterized YAML formats. This allows identical seamless deployments locally via `minikube` or remotely via EKS/GKE platforms.
  
- **Challenge:** Avoiding Disruption during Kubernetes Syncing.
  - **Mitigation:** Enforced proper Configuration probes: `readinessProbe` and `livenessProbe`. Without readiness probes, Kubernetes would immediately kill the old pods before the new Flask pods actually bound to port `5000`, causing split-second outages. The `readinessProbe` checks `/health` preventing dropped traffic.

## 3. Key Automation Outcomes

1. **Test-Driven Velocity**: Pushing into the repository validates code dynamically. The developer spends 0 manual hours manually verifying routes or database models via Postman.
2. **Deterministic Releases**: Because builds exist as immutable Docker images pushed to Docker Hub registry, a catastrophic production crash allows immediate rollback to the previous `#build` tag directly via `kubectl rollout undo` without recompiling source.
3. **Cloud Native**: The `app.py` payload went from being tied physically to a host operating system to platform-agnostic portability. Scalability only requires tweaking `replicas:` inside the `deployment.yaml` document.
