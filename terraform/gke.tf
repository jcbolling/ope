data "google_compute_network" "vpc" {
  name = "default"
}

data "google_compute_subnetwork" "subnet" {
  name = "default"
}

resource "google_container_cluster" "primary" {
  provider = google-beta

  name     = "${var.project_id}-gke"
  location = var.region

  enable_l4_ilb_subsetting = true
  remove_default_node_pool = true
  initial_node_count       = 1

  network    = data.google_compute_network.vpc.name
  subnetwork = data.google_compute_subnetwork.subnet.name
}

resource "google_container_node_pool" "primary_nodes" {
  name       = "np-default"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  node_count = var.gke_num_nodes

  node_config {
    service_account = "kubernetes@${var.project_id}.iam.gserviceaccount.com"
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = {
      env = var.project_id
    }

    resource_labels = {
      "goog-gke-node-pool-provisioning-model" = "on-demand"
    }

    kubelet_config {
      cpu_cfs_quota      = false
      cpu_manager_policy = "none"
    }

    machine_type = "n1-standard-1"
    tags         = ["gke-node", "${var.project_id}-gke"]
    metadata = {
      disable-legacy-endpoints = "true"
    }
  }
}

resource "google_container_node_pool" "rogue_node_pool" {
  name    = "np-preemptible"
  cluster = google_container_cluster.primary.name
}
