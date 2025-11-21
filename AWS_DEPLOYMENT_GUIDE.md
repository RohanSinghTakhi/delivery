# AWS Deployment Guide – MedEx Delivery Backend

This walkthrough shows how to host the FastAPI + MongoDB backend on AWS using common managed services. It’s written for beginners—follow it end-to-end to get a production-ready environment.

---

## 1. Architecture Overview

| Component | AWS Service | Purpose |
|-----------|-------------|---------|
| FastAPI app | **Amazon ECS (Fargate)** or **EC2** | Runs the backend container |
| Static uploads | **Amazon S3 + CloudFront** *(optional)* | Store proof-of-delivery files |
| Database | **Amazon DocumentDB** *(MongoDB-compatible)* or self-managed MongoDB on EC2 | Order, driver, vendor data |
| Secrets/env vars | **AWS Secrets Manager** or **SSM Parameter Store** | JWT keys, DB URL, Google API key, Woo sync secret |
| Load balancing | **Application Load Balancer (ALB)** | HTTPS termination + routing |
| WooCommerce bridge | WordPress plugin + `/api/woocommerce/*` endpoints | Sync vendor/orders from WooCommerce |
| Logs & monitoring | **CloudWatch Logs / Metrics** | View app logs & health alarms |
| CI/CD (optional) | **AWS CodePipeline + CodeBuild** or GitHub Actions | Automated deployments |

> ⚠️ If you prefer simplicity, you can start with a single EC2 instance running both FastAPI and MongoDB. The rest of this guide assumes a containerized app with a managed database.

---

## 2. Prerequisites

- AWS account with administrative access.
- Docker installed locally.
- AWS CLI configured (`aws configure`) with access key/secret.
- Domain name (optional but recommended) managed in Route 53.
- TLS certificate (ACM) for HTTPS.

---

## 3. Containerize the Backend

1. **Add a Dockerfile** (if not already present):
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY backend/requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY backend /app
   ENV PYTHONUNBUFFERED=1
   CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Build & test locally**:
   ```bash
   docker build -t medex-backend .
   docker run --env-file backend/.env -p 8000:8000 medex-backend
   ```

3. **Push to ECR**:
   ```bash
   aws ecr create-repository --repository-name medex-backend
   aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
   docker tag medex-backend <account>.dkr.ecr.<region>.amazonaws.com/medex-backend:latest
   docker push <account>.dkr.ecr.<region>.amazonaws.com/medex-backend:latest
   ```

---

## 4. Provision the Database

### Option A: Amazon DocumentDB (recommended)
1. Create a DocumentDB cluster (MongoDB-compatible).
2. Enable TLS.
3. Note the connection string (`mongodb://username:password@docdb-endpoint:27017/?tls=true`).
4. Add security group rules to allow inbound connections from ECS tasks/EC2.

### Option B: Self-managed MongoDB on EC2
1. Launch EC2 (Ubuntu).
2. Install MongoDB (`sudo apt install -y mongodb-org`).
3. Configure:
   - Bind to private IP.
   - Create admin user.
   - Enable authentication & TLS if possible.
4. Restrict security group to allow access only from the app’s security group.

---

## 5. Store Secrets & Config

Use **AWS Secrets Manager** or **SSM Parameter Store** to hold:
- `MONGO_URL`
- `DB_NAME`
- `JWT_SECRET_KEY`
- `GOOGLE_MAPS_API_KEY`
- `WOOCOMMERCE_SYNC_SECRET`
- `UPLOAD_DIR` (set to `/data/uploads` if using EFS/S3 mount)

Example via SSM:
```bash
aws ssm put-parameter --name "/medex/MONGO_URL" --type "SecureString" --value "mongodb://..."
```

In ECS/EC2 user data, fetch them using the IAM role.

---

## 6. Deploy the Application

### Option A: ECS Fargate (serverless containers)
1. Create an ECS cluster (Fargate).
2. Set up task definition:
   - Container image: ECR URI.
   - CPU/RAM: e.g., 0.5 vCPU / 1GB.
   - Environment variables: pull from Secrets Manager/SSM.
   - Port mapping: container 8000.
3. Networking:
   - Assign to a VPC with public subnets (if using ALB) and private subnets (recommended).
   - Attach security group allowing inbound from ALB on 8000.
4. Create an Application Load Balancer:
   - Listener on 443 (HTTPS).
   - Target group: ECS service.
   - ACM certificate for your domain.
5. Update DNS (Route 53) to point your domain (e.g., `api.medex.example.com`) to the ALB.

### Option B: EC2 (manual)
1. Launch EC2 (Ubuntu) with security group allowing HTTPS + SSH.
2. Install Docker & docker-compose.
3. Pull image from ECR, run container:
   ```bash
   docker run -d --env-file .env \
     -p 80:8000 --name medex-backend \
     <account>.dkr.ecr.<region>.amazonaws.com/medex-backend:latest
   ```
4. Use Nginx/ALB in front for HTTPS termination.

---

## 7. File Upload Strategy

- **Local storage** on ECS Fargate is ephemeral. Options:
  1. **Amazon S3**: Update `utils/file_handler.py` to save files directly to S3 (recommended).
  2. **EFS volume**: Mount EFS to the ECS task and set `UPLOAD_DIR` to the mount path.
  3. **EC2**: Use attached EBS volume and point `UPLOAD_DIR` to `/data/uploads`.

If you keep WordPress/Hostinger for proof-of-delivery assets, you can also push files there via API.

---

## 8. Monitoring & Scaling

1. **CloudWatch Logs**:
   - ECS task definition → enable log driver `awslogs`.
   - Watch `/aws/ecs/medex-backend`.
2. **CloudWatch Alarms**:
   - High CPU, memory, 5XX errors on ALB.
3. **Auto Scaling**:
   - ECS: configure target tracking (e.g., 60% CPU).
   - EC2: use ASG with launch template (if not on Fargate).
4. **Backups**:
   - DocumentDB automated snapshots.
   - If self-managed MongoDB, schedule `mongodump` to S3.

---

## 9. CI/CD (Optional but recommended)

### GitHub Actions Example
```yaml
name: Deploy Backend
on:
  push:
    branches: [main]
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - uses: aws-actions/amazon-ecr-login@v2
      - run: |
          docker build -t medex-backend .
          docker tag medex-backend:latest $ECR_REPO:latest
          docker push $ECR_REPO:latest
      - run: |
          aws ecs update-service --cluster medex-cluster \
            --service medex-backend-service --force-new-deployment
```

---

## 10. Final Checklist

1. ✅ Backend container pushed to ECR.
2. ✅ MongoDB (DocumentDB or EC2) reachable from ECS/EC2.
3. ✅ Secrets stored in SSM/Secrets Manager and injected as env vars.
4. ✅ ECS service or EC2 instance running FastAPI, fronted by ALB + HTTPS.
5. ✅ Upload storage decided (S3/EFS/EBS) and `UPLOAD_DIR` updated.
6. ✅ CloudWatch logs and basic alarms configured.
7. ✅ DNS pointing to ALB domain (e.g., `api.medex.example.com`).
8. ✅ WordPress plugin configured to call `/api/woocommerce/orders/sync` and `/status` with the shared secret.
9. ✅ Test the live flow (orders, drivers, vendor views) against the AWS endpoint before giving it to app developers.

Once these steps are complete, you have a production-ready AWS deployment for the MedEx backend. Add route optimization, real-time sockets, and WooCommerce webhooks as needed—they will work the same way on AWS. If you’d like infrastructure-as-code (Terraform/CloudFormation) templates later, we can script those as well.




