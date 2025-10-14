pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'web-scraper'
        DEPLOY_PATH = '/home/web-scraper'
        DOCKER_COMPOSE_FILE = 'docker-compose.yml'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code from GitHub...'
                git branch: 'main',
                    url: 'https://github.com/mallelavamshi/web-scraper.git',
                    credentialsId: 'github-credentials'
            }
        }
        
        stage('Verify Files') {
            steps {
                script {
                    sh '''
                        echo "Verifying project files..."
                        ls -la
                        cat requirements.txt
                    '''
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                echo 'Building Docker image...'
                script {
                    sh '''
                        docker build -t ${DOCKER_IMAGE}:latest .
                        docker tag ${DOCKER_IMAGE}:latest ${DOCKER_IMAGE}:${BUILD_NUMBER}
                    '''
                }
            }
        }
        
        stage('Stop Old Container') {
            steps {
                echo 'Stopping old container if exists...'
                script {
                    sh '''
                        if [ $(docker ps -q -f name=web-scraper-app) ]; then
                            echo "Stopping running container..."
                            docker-compose down
                        else
                            echo "No running container found"
                        fi
                    '''
                }
            }
        }
        
        stage('Deploy New Container') {
            steps {
                echo 'Deploying new container...'
                script {
                    sh '''
                        docker-compose up -d
                        echo "Waiting for container to start..."
                        sleep 5
                        docker ps | grep web-scraper-app
                    '''
                }
            }
        }
        
        stage('Health Check') {
            steps {
                echo 'Performing health check...'
                script {
                    sh '''
                        if [ $(docker ps -q -f name=web-scraper-app -f status=running) ]; then
                            echo "✓ Container is running"
                            docker logs --tail 20 web-scraper-app
                        else
                            echo "✗ Container failed to start"
                            exit 1
                        fi
                    '''
                }
            }
        }
        
        stage('Clean Up Old Images') {
            steps {
                echo 'Cleaning up old Docker images...'
                script {
                    sh '''
                        docker image prune -f
                        echo "✓ Cleanup complete"
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo '✓ Deployment successful!'
            emailext (
                subject: "Jenkins Build #${BUILD_NUMBER} - SUCCESS",
                body: "Web Scraper deployed successfully!",
                to: "your-email@example.com"
            )
        }
        failure {
            echo '✗ Deployment failed!'
            emailext (
                subject: "Jenkins Build #${BUILD_NUMBER} - FAILED",
                body: "Web Scraper deployment failed. Check logs.",
                to: "your-email@example.com"
            )
        }
    }
}
