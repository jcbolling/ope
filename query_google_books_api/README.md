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

### Problem 3: Variable Naming Inconsistency

**Issue:** Variable called `raw_books` in main but `results` in function parameter
- **Solution:** Renamed to `results` throughout for consistency

### Enhancement 1: CLI Arguments

**Improvement:** Added ability to pass search term as command-line argument

```python
search_term = sys.argv[1] if len(sys.argv) > 1 else error_handling
```

### Enhancement 2: Add Book URLs to Results

**Improvement:** Constructed Google Books website URL using book ID

  ```python
  book_url = f'https://books.google.com/books?id={book_id}'
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

## Part 6: Running the script on a Ubuntu-based Cloud Instance

To run the script on a Ubunti-based Cloud Instance the following commands should be used to install and configure prerequsites:

```bash
# Install the python3.10-venv package

sudo apt install python3.10-venv

# Create and activate a virtual environment

python3 -m venv venv
source venv/bin/activate

# Install requirements with pip

pip install --no-cache-dir -r requirements.txt

# Create and verify required environment variable

export GOOGLE_BOOKS_API_KEY
echo $GOOGLE_BOOKS_API_KEY
```

Finally, verify the script functions as expected by running:

`python3 query_google_books_api.py Kubernetes`

The script should produce output similar to the following:

```bash
[2026-06-26 19:54:30.928278]: Fetching up to 25 results for 'Kubernetes' from Google Books...

+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|   # | Book Title                                            | Author(s)                                                  | Publication Date   | URL     |
+=====+=======================================================+============================================================+====================+================================================+
|   1 | Certified Kubernetes Administrator (CKA) Exam Guid... | Melony Qin, Brendan Burns, Mark Whitby, Alessandro Vozza   | 2022-11-04         | https://books.google.com/books?id=SzaVEAAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|   2 | Modern Kubernetes: From Core Concepts to Intellige... | Bablu Kumar, Anshul Verma, Pradeepika Verma                | 2026-02-05         | https://books.google.com/books?id=Rz6_EQAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|   3 | The Kubernetes Bible                                  | Gineesh Madapparambath, Russ McKendrick                    | 2024-11-29         | https://books.google.com/books?id=oiU0EQAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|   4 | Acing the Certified Kubernetes Administrator Exam     | Chad Crowell                                               | 2023-12-26         | https://books.google.com/books?id=ZtjWEAAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|   5 | Mastering Kubernetes                                  | Gigi Sayfan                                                | 2020-06-30         | https://books.google.com/books?id=ZK7uDwAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|   6 | Kubernetes Anti-Patterns                              | Govardhana Miriyala Kannaiah                               | 2024-06-21         | https://books.google.com/books?id=SBUMEQAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|   7 | Mastering Kubernetes: Advanced Deployment Strategi... | Adam Jones                                                 | 2025-01-09         | https://books.google.com/books?id=Qoo9EQAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|   8 | Production Kubernetes                                 | Josh Rosso, Rich Lander, Alex Brand, John Harris           | 2021-03-16         | https://books.google.com/books?id=WLIlEAAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|   9 | Big Data on Kubernetes                                | Neylson Crepalde                                           | 2024-07-19         | https://books.google.com/books?id=1zUQEQAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|  10 | Quick Start Kubernetes                                | Nigel Poulton                                              | 2023-05-26         | https://books.google.com/books?id=tlAD0AEACAAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|  11 | Kubernetes for Full-Stack Developers                  | N/A                                                        | 2020-02-04         | https://books.google.com/books?id=oy3RDwAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|  12 | Mastering Kubernetes in Production                    | Peter Johnson                                              | 2024-09-16         | https://books.google.com/books?id=slQ3EQAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|  13 | Kubernetes for Absolute Beginners                     | Brando Marzio Sabatini                                     | 2026-05-19         | https://books.google.com/books?id=pQ_WEQAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|  14 | SQL Server on Kubernetes                              | Anthony E. Nocentino, Ben Weissman                         | 2021               | https://books.google.com/books?id=ZpZ8zwEACAAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|  15 | Quick Start Kubernetes                                | Nigel Poulton                                              | 2023-07-05         | https://books.google.com/books?id=5bjJEAAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|  16 | Getting Started with Istio Service Mesh               | Rahul Sharma, Avinash Singh                                | 2019-12-05         | https://books.google.com/books?id=qBvCDwAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|  17 | Cloud Native DevOps with Kubernetes                   | Justin Domingus, John Arundel                              | 2022-03-16         | https://books.google.com/books?id=R85kEAAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|  18 | End-to-End Automation with Kubernetes and Crosspla... | Arun Ramakani                                              | 2022-08-12         | https://books.google.com/books?id=zwN6EAAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|  19 | Kubernetes and Docker - An Enterprise Guide           | Scott Surovich, Marc Boorshtein                            | 2020-11-06         | https://books.google.com/books?id=0UEIEAAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|  20 | Kubernetes for Developers                             | William Denniss                                            | 2024-03-19         | https://books.google.com/books?id=6144EAAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|  21 | Kubernetes: Up and Running                            | Brendan Burns, Joe Beda, Kelsey Hightower, Lachlan Evenson | 2022-08-02         | https://books.google.com/books?id=KeB-EAAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|  22 | Understanding Kubernetes in a visual way              | Aurélie Vache                                              | 2020-05-31         | https://books.google.com/books?id=yWzqDwAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|  23 | The KCNA Book                                         | Nigel Poulton                                              | 2023-06-20         | https://books.google.com/books?id=VyFOEQAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|  24 | From Containers to Kubernetes with Node.js            | Kathleen Juell                                             | 2020-05-08         | https://books.google.com/books?id=ZUjiDwAAQBAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
|  25 | Kubernetes                                            | Sheldon Miles                                              | 2020-02-13         | https://books.google.com/books?id=M4VmzQEACAAJ |
+-----+-------------------------------------------------------+------------------------------------------------------------+--------------------+------------------------------------------------+
```