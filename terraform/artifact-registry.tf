resource "google_artifact_registry_repository" "docker" {
  repository_id = "dev-registry-1"
  location      = "us-central1"  # https://github.com/hashicorp/terraform-provider-google/issues/10436
  format        = "DOCKER"
}
