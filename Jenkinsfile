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

        stage('Kubernetes Deploy') {
            steps {
                script {
                    sh '''
                    # 1. Download the kubectl binary into the current workspace
                    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
                    
                    # 2. Make it executable
                    chmod +x ./kubectl
                    
                    # 3. Use the local binary (./kubectl) instead of the system one
                    export KUBECONFIG=/var/lib/jenkins/.kube/config
                    
                    sed -i "s|DOCKER_IMAGE_PLACEHOLDER|${DOCKER_IMAGE}:${DOCKER_TAG}|g" k8s/deployment.yaml
                    
                    ./kubectl apply -f k8s/deployment.yaml
                    ./kubectl apply -f k8s/service.yaml
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
