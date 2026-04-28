pipeline {
    agent any
    
    environment {
        // Defines the Docker image repository explicitly
        DOCKER_IMAGE = "aceest-fitness-gym-cicd"
        DOCKER_TAG = "${env.BUILD_ID}"
        DOCKER_CREDS_ID = "dockerhub-credentials" // Jenkins credentials ID for Docker Hub
        CLUSTER_ENV = "minikube"
        // Force Python to not write .pyc files and buffer output for cleaner logs
        PYTHONDONTWRITEBYTECODE = 1
        PYTHONUNBUFFERED = 1
    }

    stages {
        stage('Checkout') {
            steps {
                echo "Checking out Git repository..."
                checkout scm
            }
        }

        stage('Unit Tests') {
        steps {
                // Use 'sh' to verify python3 is there first
                sh 'python3 --version' 
                sh 'python3 -m venv venv'
                sh '. venv/bin/activate && pip install -r requirements.txt'
                sh '. venv/bin/activate && pytest --junitxml=results.xml'
            }
        }
        stage('SonarQube Code Analysis') {
            steps {
                echo "Executing SonarQube static code analysis..."
                script {
                    // This version is less 'picky' about the internal ID
                    def scannerHome = tool 'sonar-scanner' 
                    //def nodePath = "/usr/local/bin/node"
                    
                    withSonarQubeEnv('sonarqube-server') {
                        sh """
                        ${scannerHome}/bin/sonar-scanner \
                        -Dsonar.sources=. \
                        -Dsonar.tests=tests \
                        -Dsonar.exclusions=tests/**,**/*.js,**/*.ts,**/*.css,**/*.html \
                        -Dsonar.language.js.skip=true \
                        -Dsonar.language.ts.skip=true \
                        -Dsonar.language.css.skip=true
                        """
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

        stage('Docker Image Assembly') {
            steps {
                echo "==> Building Docker image: ${DOCKER_IMAGE}:${DOCKER_TAG}"
                sh "docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} -t ${DOCKER_IMAGE}:latest ."
                
                echo "==> Verifying Docker image..."
                sh "docker images ${DOCKER_IMAGE}:${DOCKER_TAG}"
                sh "docker images ${DOCKER_NAME}"
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
