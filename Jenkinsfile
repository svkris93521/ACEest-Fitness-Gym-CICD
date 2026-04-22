pipeline {
    agent any

    tools {
        // Define the SonarQube Scanner tool for static code analysis
        "sonar-scanner" "sonar-scanner"
    }
    
    environment {
        // Defines the Docker image repository explicitly
        DOCKER_IMAGE = "svkris93521/aceest-fitness"
        DOCKER_TAG = "${env.BUILD_ID}"
        DOCKER_CREDS_ID = "dockerhub-credentials"
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
                // Requires SonarQube Scanner plugin and configuration in Jenkins
                echo "Executing SonarQube static code analysis..."
                withSonarQubeEnv('sonarqube-server') {
                    sh 'sonar-scanner'
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

        stage('Kubernetes Deploy - Rolling Update') {
            steps {
                echo "Deploying to Kubernetes using Rolling Update strategy..."
                // Ensure kubectl context is properly set to Minikube or Cloud provider
                sh '''
                sed -i "s|DOCKER_IMAGE_PLACEHOLDER|${DOCKER_IMAGE}:${DOCKER_TAG}|g" k8s/deployment.yaml
                kubectl apply -f k8s/deployment.yaml
                kubectl apply -f k8s/service.yaml
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
