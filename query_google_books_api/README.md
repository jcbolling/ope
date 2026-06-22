# Project - Google Books API Search Script Kubernetes Deployment

## Overview

Implemented a containerized Google Books API search script written in Python, deployed it as a Kubernetes CronJob, and troubleshot various authentication and deployment issues.

---

## Part 1: Python Script Development

### Problem 1: 404 Error on API Endpoint

**Issue:** Incorrect API endpoint was hardcoded

- **Original:** `https://googleapis.com`
- **Fix:** Changed to `https://www.googleapis.com/books/v1/volumes`

### Problem 2: 429 Rate Limiting Error

**Issue:** Getting "Too Many Requests" responses
- **Cause:** No API key provided; unauthenticated requests have strict rate limits
- **Solution:** Added Google Books API key to requests

  ```python
  API_KEY = 'your_api_key'
  params = {'key': API_KEY, ...}
  ```

### Problem 3: Need Book URLs in Results

**Issue:** User wanted to include links to books in output
- **Initial Solution:** Used `selfLink` from API response
- **Final Solution:** Constructed Google Books website URL using book ID

  ```python
  book_url = f'https://books.google.com/books?id={book_id}'
  ```

### Problem 4: Variable Naming Inconsistency

**Issue:** Variable called `raw_books` in main but `results` in function parameter
- **Solution:** Renamed to `results` throughout for consistency

### Enhancement: CLI Arguments

**Improvement:** Added ability to pass search term as command-line argument

```python
search_term = sys.argv[1] if len(sys.argv) > 1 else error_handling
```

---

## Part 2: Containerization

### Decision: venv vs Docker Build

**Recommendation:** Always build Python dependencies **inside** the Dockerfile, not package local venv
- **Why:** Local venv contains binaries specific to macOS; Docker runs Linux
- **Approach:** Use requirements.txt and `pip install` in Dockerfile

### Dockerfile Created
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY query_google_books_api.py .
ENTRYPOINT ["python", "query_google_books_api.py"]
```

### Problem: 503 Error in Container

**Issue:** Script worked locally but got 503 Service Unavailable in Docker
- **Cause:** Eventually traced to hardcoded arguments and authentication issues
- **Solution:** Fix authentication and ensure proper image tag usage

---

## Part 3: Kubernetes Deployment

### CronJob Implementation

Created a Kubernetes CronJob to run the script on a schedule:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: google-books-search
  namespace: google-books-search
spec:
  schedule: "*/5 * * * *"  # Every 5 minutes
  jobTemplate:
    spec:
      template:
        spec:
          imagePullSecrets:
          - name: gcr-auth-details
          containers:
          - name: google-books
            image: gcr.io/ope-take-home/google-books-search:v1.0.0
            args: ["Kubernetes"]
```

### Key CronJob Features

- **New pod per execution:** A fresh pod is created for each schedule trigger
- **History limits:** Keep last 5 successful + 3 failed jobs
- **Output:** Results accessible via `kubectl logs`

---

## Part 4: Image Registry & Authentication

### Multi-Architecture Build

Built Docker image for both AMD64 and ARM64:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t gcr.io/ope-take-home/google-books-search:v1.0.0 \
  --push \
  .
```

### GCR Authentication Challenge

**Problem:** Organization has service account key creation disabled
**Options considered:**
1. Enable Workload Identity (GKE-only, requires cluster changes)
2. Use ImagePullSecret with personal credentials ✅ (chosen)
3. Request admin to create key

### ImagePullSecret Setup

```bash
gcloud auth configure-docker gcr.io
kubectl create secret generic gcr-auth-details \
  --from-file=.dockerconfigjson=$HOME/.docker/config.json \
  --type=kubernetes.io/dockerconfigjson \
  -n google-books-search
```

### Problem: Credential Helper Not Working in Pod

**Issue:** Docker config used `credHelpers` instead of actual credentials
- **Problem:** Credential helpers only work on local machine, not in container
- **Solution:** Created secret with actual access token (note: tokens expire after ~1 hour)

---

## Part 5: Troubleshooting Deployment

### Problem: Duplicate Arguments

**Issue:** Script received error about converting "Kubernetes" to int

```
ValueError: invalid literal for int() with base 10: 'Kubernetes'
```

**Root cause:** 
- Dockerfile hardcoded `ENTRYPOINT ["python", "query_google_books_api.py", "Kubernetes"]`
- CronJob also passed `args: ["Kubernetes"]`
- Script received 2 "Kubernetes" args and tried to parse the 2nd as an int

**Solution:** Remove hardcoded argument from Dockerfile

```dockerfile
ENTRYPOINT ["python", "query_google_books_api.py"]
```

### Problem: Image Updates Not Pulling Automatically

**Issue:** CronJob continued using old image after rebuild
- **Cause:** Using `:latest` tag can have caching issues
- **Solutions:**
  1. Use versioned tags (recommended): `v1.0.0`, `v1.0.1`
  2. Set `imagePullPolicy: Always` in container spec
  3. Delete and recreate CronJob

**Adopted:** Semantic versioning for image tags
