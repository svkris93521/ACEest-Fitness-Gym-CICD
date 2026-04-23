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
                    waitForQualityGate abortPipeline: true
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
                # Wait for the application to be ready (simple sleep or implement a more robust wait)
                sleep 30
                # Run integration tests (this is a placeholder, implement actual tests)
                # For example, you could use curl to hit the service endpoint and check responses
                curl -s http://$(./minikube ip):$(./kubectl get svc aceest-service -o jsonpath='{.spec.ports[0].nodePort}')/health || exit 1
                #print the url for manual testing
                echo "Application URL: http://$(./minikube ip):$(./kubectl get svc aceest-service -o jsonpath='{.spec.ports[0].nodePort}')"
                '''
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
