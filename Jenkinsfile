pipeline {
    agent any
    
    environment {
        // Defines the Docker image repository explicitly
        DOCKER_IMAGE = "svkris/aceest-fitness"
        DOCKER_TAG = "${env.BUILD_ID}"
        DOCKER_CREDS_ID = "dockerhub-credentials" // Jenkins credentials ID for Docker Hub
        CLUSTER_ENV = "minikube"
    }

    stages {
        stage('Checkout') {
            steps {
                echo "Checking out Git repository..."
                checkout scm
            }
        }

        stage('Unit Testing') {
            steps {
                echo "Running unit tests using Pytest..."
                sh '''
                python -m venv venv
                . venv/bin/activate
                pip install -r requirements.txt
                pytest tests/ --junitxml=reports/test-report.xml
                '''
            }
            post {
                always {
                    junit 'reports/test-report.xml'
                }
            }
        }

        stage('SonarQube Code Analysis') {
            steps {
                echo "Executing SonarQube static code analysis..."
                script {
                    // This version is less 'picky' about the internal ID
                    def scannerHome = tool 'sonar-scanner' 
                    
                    withSonarQubeEnv('sonarqube-server') {
                        sh "${scannerHome}/bin/sonar-scanner"
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                echo "Waiting for SonarQube Quality Gate approval..."
                timeout(time: 1, unit: 'HOURS') {
                    waitForQualityGate abortPipeline: false
                }
            }
        }

        stage('Docker Build') {
            steps {
                echo "Building Docker Image: ${DOCKER_IMAGE}:${DOCKER_TAG}"
                sh "docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} -t ${DOCKER_IMAGE}:latest ."
            }
        }

        stage('Docker Push') {
            steps {
                echo "Pushing Docker Image to Docker Hub registry..."
                withCredentials([usernamePassword(credentialsId: "${DOCKER_CREDS_ID}", passwordVariable: 'DOCKER_PASS', usernameVariable: 'DOCKER_USER')]) {
                    sh "docker login -u ${DOCKER_USER} -p ${DOCKER_PASS}"
                    sh "docker push ${DOCKER_IMAGE}:${DOCKER_TAG}"
                    sh "docker push ${DOCKER_IMAGE}:latest"
                }
            }
        }

        stage('Kubernetes Infrastructure & Deploy') {
            steps {
                script {
                    sh '''
                    # 1. Install kubectl locally in workspace if missing
                    if [ ! -f "./kubectl" ]; then
                        echo "Downloading kubectl..."
                        curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
                        chmod +x ./kubectl
                    fi

                    # 2. Install minikube locally in workspace if missing
                    if [ ! -f "./minikube" ]; then
                        echo "Downloading minikube..."
                        curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
                        mv minikube-linux-amd64 minikube
                        chmod +x ./minikube
                    fi

                    # 3. Start Minikube (using Docker driver)
                    # We use --wait=all to ensure the cluster is ready before we deploy
                    echo "Starting Minikube..."
                    ./minikube start --driver=docker --wait=all

                    # 4. Prepare the Deployment
                    echo "Updating deployment manifest with image ${DOCKER_IMAGE}:${DOCKER_TAG}..."
                    sed -i "s|DOCKER_IMAGE_PLACEHOLDER|${DOCKER_IMAGE}:${DOCKER_TAG}|g" k8s/deployment.yaml

                    # 5. Execute Deployment
                    # We use the local kubectl and bypass validation for maximum stability on the VM
                    echo "Applying manifests to Minikube..."
                    ./kubectl apply -f k8s/deployment.yaml --validate=false
                    ./kubectl apply -f k8s/service.yaml --validate=false
                    
                    # 6. Final Status Check
                    ./kubectl get pods
                    '''
                }
            }
        }

            // Test if the application is running correctly in the cluster (optional)
        stage('Integration Testing') {
            steps {
                echo "Running integration tests against the deployed application..."
                sh '''
                # 1. Ensure we are using the right config
                export KUBECONFIG=/var/lib/jenkins/.kube/config
                
                # 2. Define the service name (UPDATE THIS to match your k8s/service.yaml)
                SERVICE_NAME="aceest-fitness-service"

                # 3. Wait for the service to actually appear in K8s
                echo "Waiting for ${SERVICE_NAME} to be available..."
                MAX_RETRIES=10
                COUNT=0
                while ! ./kubectl get svc $SERVICE_NAME >/dev/null 2>&1; do
                    if [ $COUNT -eq $MAX_RETRIES ]; then
                    echo "Error: Service $SERVICE_NAME not found after waiting."
                    exit 1
                    fi
                    echo "Service not found yet, retrying in 10s..."
                    sleep 10
                    COUNT=$((COUNT + 1))
                done

                # 4. Get the URL and Port
                MINIKUBE_IP=$(./minikube ip)
                NODE_PORT=$(./kubectl get svc $SERVICE_NAME -o jsonpath='{.spec.ports[0].nodePort}')
                APP_URL="http://${MINIKUBE_IP}:${NODE_PORT}"

                echo "Application URL: ${APP_URL}"

                # 5. Run the actual health check
                # -f makes curl fail on 4xx/5xx errors, -s is silent
                curl -f -s "${APP_URL}/health" || { echo "Health check failed!"; exit 1; }
                
                echo "Integration Test Passed!"
                '''
            }
        }

        stage('Expose Application') {
            steps {
                script {
                    sh '''
                    # 1. Kill any old forwards
                    pkill -f "port-forward" || true
                    
                    # 2. Crucial: Tell Jenkins NOT to kill background processes after the stage
                    export JENKINS_NODE_COOKIE=dontKillMe
                    export KUBECONFIG=/var/lib/jenkins/.kube/config
                    
                    # 3. Use the LOCAL ./kubectl we downloaded in the earlier stage
                    # Change 80 to 5000 or 8000 if your Flask/Django app uses those!
                    nohup ./kubectl port-forward svc/aceest-fitness-service 8085:80 --address 0.0.0.0 > pf.log 2>&1 &
                    
                    # 4. Wait and verify it actually stayed alive
                    sleep 5
                    if pgrep -f "port-forward" > /dev/null; then
                        MK_URL=$(curl -s ifconfig.me)
                        echo "--------------------------------------------------------"
                        echo "SUCCESS: App exposed at http://$(curl -s ifconfig.me):8085"
                        echo "--------------------------------------------------------"
                        curl -f -s "http://127.0.0.1:8085/health" || { echo "Health check failed!"; exit 1; }
                        echo "Health check passed on exposed URL!"
                    else
                        echo "ERROR: Port-forward failed to start. Check pf.log:"
                        cat pf.log
                        exit 1
                    fi
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo "CI/CD Pipeline executed successfully!"
        }
        failure {
            echo "Pipeline Failed. Please review the logs."
        }
    }
}
