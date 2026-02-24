import datetime
import logging

import kubernetes
from kubernetes.client.rest import ApiException

from celery import shared_task

from cabotage.server import db, kubernetes as kubernetes_ext
from cabotage.server.models.projects import (
    Application,
    ObservabilitySnapshot,
)

logger = logging.getLogger(__name__)


def _parse_cpu(value):
    """Parse K8s CPU value (e.g. '245230n', '250m', '1') to millicores."""
    if not value:
        return 0
    value = str(value)
    if value.endswith("n"):
        return int(value[:-1]) / 1_000_000
    if value.endswith("m"):
        return int(value[:-1])
    return float(value) * 1000


def _parse_memory(value):
    """Parse K8s memory value (e.g. '178956970', '256Mi', '1Gi') to bytes."""
    if not value:
        return 0
    value = str(value)
    suffixes = {"Ki": 1024, "Mi": 1024**2, "Gi": 1024**3, "Ti": 1024**4}
    for suffix, multiplier in suffixes.items():
        if value.endswith(suffix):
            return int(value[: -len(suffix)]) * multiplier
    # Plain integer = bytes
    return int(value)


@shared_task()
def collect_observability_snapshots():
    """Collect CPU/memory metrics for all active applications."""
    applications = Application.query.filter(
        Application.process_counts != {},
        Application.process_counts.isnot(None),
    ).all()

    active_apps = [
        app
        for app in applications
        if app.process_counts and any(v > 0 for v in app.process_counts.values())
    ]

    if not active_apps:
        return

    api_client = kubernetes_ext.kubernetes_client
    custom_api = kubernetes.client.CustomObjectsApi(api_client)
    core_api = kubernetes.client.CoreV1Api(api_client)

    for app in active_apps:
        try:
            _collect_for_app(app, custom_api, core_api)
        except Exception:
            logger.exception("Failed to collect observability for app %s", app.id)

    db.session.commit()


def _collect_for_app(app, custom_api, core_api):
    namespace = app.project.organization.slug
    label_selector = (
        f"organization={app.project.organization.slug},"
        f"project={app.project.slug},"
        f"application={app.slug}"
    )

    total_cpu_m = 0
    total_memory_bytes = 0
    pod_count = 0
    restart_count = 0

    # Get pod list for restart counts
    try:
        pods = core_api.list_namespaced_pod(namespace, label_selector=label_selector)
        pod_count = len(pods.items)
        for pod in pods.items:
            if pod.status and pod.status.container_statuses:
                for cs in pod.status.container_statuses:
                    restart_count += cs.restart_count or 0
    except ApiException:
        logger.debug("Could not list pods for app %s", app.id)

    # Get metrics from metrics.k8s.io
    try:
        metrics = custom_api.list_namespaced_custom_object(
            "metrics.k8s.io",
            "v1beta1",
            namespace,
            "pods",
            label_selector=label_selector,
        )
        for pod_metric in metrics.get("items", []):
            for container in pod_metric.get("containers", []):
                usage = container.get("usage", {})
                total_cpu_m += _parse_cpu(usage.get("cpu", "0"))
                total_memory_bytes += _parse_memory(usage.get("memory", "0"))
    except ApiException as exc:
        if exc.status == 404:
            logger.debug("metrics-server not available for app %s", app.id)
        else:
            logger.warning("Metrics API error for app %s: %s", app.id, exc.status)

    snapshot = ObservabilitySnapshot(
        application_id=app.id,
        cpu_usage_m=total_cpu_m,
        memory_usage_bytes=total_memory_bytes,
        pod_count=pod_count,
        restart_count=restart_count,
    )
    db.session.add(snapshot)


@shared_task()
def prune_observability_snapshots():
    """Delete snapshots older than 30 days."""
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=30)
    deleted = ObservabilitySnapshot.query.filter(
        ObservabilitySnapshot.timestamp < cutoff
    ).delete()
    db.session.commit()
    logger.info("Pruned %d observability snapshots", deleted)
