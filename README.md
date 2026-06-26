# O'Reilly Platform Engineering Take Home Assignment Notes

## Task 1: Troubleshoot Kubernetes App

**Problem 1**: The application server in the container is listening on port 8080, but the pod health check and Kubernetes service associated with the application are using port 9090.

**Diagnostic commands**

```bash
kubectl describe pods pe-web-6bd6cbcc64-zlwxc -n pe-demo-app

Name:             pe-web-6bd6cbcc64-zlwxc
Namespace:        pe-demo-app
Priority:         0
Service Account:  default
Node:             gke-pe-upbeat-deer-392-np-preemptible-81ec29ff-1gqt/10.128.0.11
Start Time:       Wed, 24 Jun 2026 21:05:17 +0000
Labels:           app=pe-web
                  pod-template-hash=6bd6cbcc64
                  topology.kubernetes.io/region=us-central1
                  topology.kubernetes.io/zone=us-central1-f
Annotations:      <none>
Status:           Running
IP:               10.20.4.8
IPs:
  IP:           10.20.4.8
Controlled By:  ReplicaSet/pe-web-6bd6cbcc64
Containers:
  pe-app:
    Container ID:   containerd://1db70798372902cff04d21582d71b6fd2c50dccc23b9e26a79b67f68e24fb829
    Image:          us-central1-docker.pkg.dev/pe-upbeat-deer-392/dev-registry-1/pe-demo-app:v1
    Image ID:       us-central1-docker.pkg.dev/pe-upbeat-deer-392/dev-registry-1/pe-demo-app@sha256:65c74dbe9f78c2e1e43d36642694598f0bfa830f2fca989fb63fab36041e9376
    Port:           <none>
    Host Port:      <none>
    State:          Waiting
      Reason:       CrashLoopBackOff
    Last State:     Terminated
      Reason:       Error
      Exit Code:    2
      Started:      Wed, 24 Jun 2026 21:16:25 +0000
      Finished:     Wed, 24 Jun 2026 21:16:27 +0000
    Ready:          False
    Restart Count:  9
    Liveness:       http-get http://:9090/healthz delay=0s timeout=1s period=1s #success=1 #failure=1
    Readiness:      http-get http://:9090/healthz delay=0s timeout=1s period=1s #success=1 #failure=1
    Environment:    <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-2cpnr (ro)
Conditions:
  Type                        Status
  PodReadyToStartContainers   True
  Initialized                 True
  Ready                       False
  ContainersReady             False
  PodScheduled                True
Volumes:
  kube-api-access-2cpnr:
    Type:                    Projected (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:           kube-root-ca.crt
    Optional:                false
    DownwardAPI:             true
QoS Class:                   BestEffort
Node-Selectors:              <none>
Tolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s
                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s
Events:
  Type     Reason     Age                   From               Message
  ----     ------     ----                  ----               -------
  Normal   Scheduled  12m                   default-scheduler  Successfully assigned pe-demo-app/pe-web-6bd6cbcc64-zlwxc to gke-pe-upbeat-deer-392-np-preemptible-81ec29ff-1gqt
  Warning  Unhealthy  12m (x4 over 12m)     kubelet            spec.containers{pe-app}: Liveness probe failed: Get "http://10.20.4.8:9090/healthz": dial tcp 10.20.4.8:9090: connect: connection refused
  Warning  Unhealthy  12m (x16 over 12m)    kubelet            spec.containers{pe-app}: Readiness probe failed: Get "http://10.20.4.8:9090/healthz": dial tcp 10.20.4.8:9090: connect: connection refused
  Normal   Created    11m (x6 over 12m)     kubelet            spec.containers{pe-app}: Container created
  Normal   Started    10m (x6 over 12m)     kubelet            spec.containers{pe-app}: Container started
  Normal   Killing    10m (x6 over 12m)     kubelet            spec.containers{pe-app}: Container pe-app failed liveness probe, will be restarted
  Warning  BackOff    2m43s (x23 over 12m)  kubelet            spec.containers{pe-app}: Back-off restarting failed container pe-app in pod pe-web-6bd6cbcc64-zlwxc_pe-demo-app(95ecc808-5dcf-43c8-aea6-26db2fdef331)
  Normal   Pulled     100s (x9 over 12m)    kubelet            spec.containers{pe-app}: Container image "us-central1-docker.pkg.dev/pe-upbeat-deer-392/dev-registry-1/pe-demo-app:v1" already present on machine and can be accessed by the pod

kubectl logs pe-web-6bd6cbcc64-zlwxc -n pe-demo-app --previous
2026/06/24 21:16:25 Environment variable 'ENV' not set!
2026/06/24 21:16:25 Server listening on port 8080
```

**Solution**: Update port numbers in manifests and re-apply

```bash
candidate@dev-instance-1:~/pe-demo-app/manifests$ vim app-service.yaml

candidate@dev-instance-1:~/pe-demo-app/manifests$ vim app-deployment.yaml

candidate@dev-instance-1:~/pe-demo-app/manifests$ kubectl apply -f app-service.yaml

service/pe-web configured

candidate@dev-instance-1:~/pe-demo-app/manifests$ kubectl apply -f app-deployment.yaml
Warning: resource deployments/pe-web is missing the kubectl.kubernetes.io/last-applied-configuration annotation which is required by kubectl apply. kubectl apply should only be used on resources created declaratively by either kubectl create --save-config or kubectl apply. The missing annotation will be patched automatically.
deployment.apps/pe-web configured

candidate@dev-instance-1:~/pe-demo-app/manifests$ kubectl get pods -n pe-demo-app -w
NAME                      READY   STATUS    RESTARTS   AGE
pe-web-68d7474cb4-5pp4m   1/1     Running   0          16s
pe-web-68d7474cb4-d48rf   1/1     Running   0          8s
pe-web-68d7474cb4-kvq4v   1/1     Running   0          12s
redis-0                   1/1     Running   0          19h
redis-1                   1/1     Running   0          19h
redis-2                   1/1     Running   0          18h
redis-3                   1/1     Running   0          18h
redis-4                   1/1     Running   0          19h
redis-5                   1/1     Running   0          19h
```

**Problem 2**: The service is using the incorrect label for the selector causing the service to have no endpoints

**Diagnostic commands**

**Get pod labels**

```bash
k get pods -n pe-demo-app --show-labels
NAME                      READY   STATUS    RESTARTS   AGE     LABELS
pe-web-5595c58876-2fq8r   1/1     Running   0          10m     app=pe-web,pod-template-hash=5595c58876,topology.kubernetes.io/region=us-central1,topology.kubernetes.io/zone=us-central1-a
pe-web-5595c58876-grbb6   1/1     Running   0          9m55s   app=pe-web,pod-template-hash=5595c58876,topology.kubernetes.io/region=us-central1,topology.kubernetes.io/zone=us-central1-f
pe-web-5595c58876-jrtz9   1/1     Running   0          9m56s   app=pe-web,pod-template-hash=5595c58876,topology.kubernetes.io/region=us-central1,topology.kubernetes.io/zone=us-central1-b
```

**Check label in service manifest**

```bash
grep -A5 selector app-service.yaml
  selector:
    app: pe-webapp
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
```

**Determine how the selector is configured in the running service**

```bash
kubectl get svc pe-web -n pe-demo-app -o yaml | grep -A5 selector
      {"apiVersion":"v1","kind":"Service","metadata":{"annotations":{"networking.gke.io/load-balancer-type":"Internal"},"labels":{"app":"pe-web"},"name":"pe-web","namespace":"pe-demo-app"},"spec":{"externalTrafficPolicy":"Cluster","ports":[{"port":80,"protocol":"TCP","targetPort":8080}],"selector":{"app":"pe-webapp"},"type":"LoadBalancer"}}
    networking.gke.io/load-balancer-type: Internal
    service.kubernetes.io/backend-service: k8s2-yuz0i2hf-pe-demo-app-pe-web-sloz531w
    service.kubernetes.io/firewall-rule: k8s2-yuz0i2hf-pe-demo-app-pe-web-sloz531w
    service.kubernetes.io/firewall-rule-for-hc: k8s2-yuz0i2hf-l4-shared-hc-fw
    service.kubernetes.io/healthcheck: k8s2-yuz0i2hf-l4-shared-hc
--
  selector:
    app: pe-webapp
  sessionAffinity: None
  type: LoadBalancer
status:
  loadBalancer:
```

**Verify pe-webapp label matches no pods yielding no corresponding endpoints**

```bash
kubectl get endpoints pe-web -n pe-demo-app
Warning: v1 Endpoints is deprecated in v1.33+; use discovery.k8s.io/v1 EndpointSlice
NAME     ENDPOINTS   AGE
pe-web   <none>      19h
    
kubectl apply -f app-service.yaml

kubectl get endpoints pe-web -n pe-demo-app
Warning: v1 Endpoints is deprecated in v1.33+; use discovery.k8s.io/v1 EndpointSlice
NAME     ENDPOINTS                                       AGE
pe-web   10.20.1.12:8080,10.20.3.5:8080,10.20.4.9:8080   19h
```

**Solution**: Change app: pe-webapp to app: pe-web in app-service manifest and re-apply

**Problem 3**: The application is reachable now that the service has valid endpoints, but curl is returning a 503 due to a missing environment variable:

```bash
curl http://10.128.0.13
503 - Error due to missing environment variable!
```

The environment variable is missing because a configMap exists for the deployment, but isn't referenced in the app-deployment manifest.

**Diagnostic commands**

**Check pod logs to see if the missing environment variable is mentioned by name**

```bash
kubectl logs pe-web-68d7474cb4-d48rf -n pe-demo-app
2026/06/25 15:41:03 Environment variable 'ENV' not set!
2026/06/25 15:41:03 Server listening on port 8080
```

**Solution**: Add an env section to the container spec defining the ENV variable referencing the configMap in the app-deployment manifest and re-apply.

---

## Task 2: Manage Infrastructure with Terraform

### Import missing resources

### 1. Get the cluster name and region

```bash
gcloud container clusters list
```

### 2. Identify the rogue node pool

```bash
# Get all node pools in Google Cloud

gcloud container node-pools list --cluster pe-upbeat-deer-392-gke --region us-central1

# Get node pools Terraform knows about

terraform state list | grep node_pool
```

### 3. Write a stub resource block in `gke.tf`

```hcl
resource "google_container_node_pool" "rogue_node_pool" {
  name    = "np-preemptible"
  cluster = google_container_cluster.primary.name
}
```

### 4. Import the node pool into Terraform state

```bash
terraform import google_container_node_pool.rogue_node_pool pe-upbeat-deer-392/us-central1/pe-upbeat-deer-392-gke/np-preemptible
```

### 5. Check for drift

```bash
terraform plan
```

Reconcile any drift by updating the resource block to match the live infrastructure. In this case the `primary_nodes` resource required a `kubelet_config` block with `cpu_manager_policy = "none"`.

### 6. Apply the changes

```bash
terraform apply
```

### 7. Confirm clean state

```bash
terraform plan
```

Should return `No changes. Infrastructure is up-to-date.`
### Create CloudSQL instance

**NOTE: I attempted to create a Google Secrets Manager instance and store the randomly generated password to reflect what would likely happen in a production environment, but the API wasn't available so I fell back to outputting the password to the local terminal while also excluding Terraform state in `.gitignore` to prevent the password from being written to Git history. The GSM related resources are preserved in the following code snippet.**

**cloud-sql.tf**

```hcl
# Generate random 32 character password

resource "random_password" "postgres_password" {
  length  = 32
  special = true
}

# Create secret object in Google Secrets Manager

#resource "google_secret_manager_secret" "postgres_password" {
#  secret_id = "postgres-password"

#  replication {
#    user_managed {
#      replicas {
#        location = "us-central1"
#      }
#    }
#  }
#}

# Populate GSM object with data generated by random password resource

#resource "google_secret_manager_secret_version" "postgres_password" {
#  secret      = google_secret_manager_secret.postgres_password.id
#  secret_data = random_password.postgres_password.result
#}

# Create CloudSQL database instance

resource "google_sql_database_instance" "postgres" {
  name             = "pe-demo-postgres"
  database_version = "POSTGRES_15"
  region           = "us-central1"

  settings {
    tier = "db-f1-micro"

    insights_config {
      query_insights_enabled  = true   # Enables query analysis
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }
  }
}

# Create database on CloudSQL instance

resource "google_sql_database" "database" {
  name     = "pe-demo-db"
  instance = google_sql_database_instance.postgres.name
}

# Create pe-admin user on pe-dmeo-db database with random auto-generated password

resource "google_sql_user" "postgres_user" {
  name     = "pe-admin"
  instance = google_sql_database_instance.postgres.name
  password = random_password.postgres_password.result
}
```

**outputs.tf**

```hcl
output "region" {
  value       = var.region
  description = "GCloud Region"
}

output "project_id" {
  value       = var.project_id
  description = "GCloud Project ID"
}

output "kubernetes_cluster_name" {
  value       = google_container_cluster.primary.name
  description = "GKE Cluster Name"
}

output "kubernetes_cluster_host" {
  value       = google_container_cluster.primary.endpoint
  description = "GKE Cluster Host"
}

output "postgres_password" {
  value     = random_password.postgres_password.result
  sensitive = true
}
```

---
## Task 3: Write a Script to Pull Data From an API

See dedicated [README](https://github.com/jcbolling/ope/tree/main/query_google_books_api#readme).