import datetime
import logging

import kubernetes

from celery import shared_task

from cabotage.server import (
    db,
    kubernetes as kubernetes_ext,
)
from cabotage.server.models.projects import Deployment
from cabotage.celery.tasks.deploy import (
    deployment_is_complete,
)
from cabotage.utils.github import post_deployment_status_update

logger = logging.getLogger(__name__)


@shared_task()
def reap_pods():
    api_client = kubernetes_ext.kubernetes_client
    core_api_instance = kubernetes.client.CoreV1Api(api_client)
    pods = core_api_instance.list_pod_for_all_namespaces(
        label_selector="resident-pod.cabotage.io=true",
    )
    started_pods = [pod for pod in pods.items if pod.status.start_time is not None]
    if not started_pods:
        return
    candidate = sorted(started_pods, key=lambda pod: pod.status.start_time)[0]
    lookback = datetime.datetime.now().replace(
        tzinfo=datetime.timezone.utc
    ) - datetime.timedelta(days=7)
    if candidate.status.start_time < lookback:
        core_api_instance.delete_namespaced_pod(
            candidate.metadata.name, candidate.metadata.namespace
        )


@shared_task()
def complete_stuck_deployments():
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        minutes=2
    )
    stuck_deployments = Deployment.query.filter(
        Deployment.complete.is_(False),
        Deployment.error.is_(False),
        Deployment.job_id.isnot(None),
        Deployment.updated < cutoff,
    ).all()

    if not stuck_deployments:
        return

    api_client = kubernetes_ext.kubernetes_client
    apps_api_instance = kubernetes.client.AppsV1Api(api_client)

    for deployment in stuck_deployments:
        release = deployment.release_object
        if release is None:
            continue
        namespace = release.application.project.organization.slug
        service_account_name = (
            f"{release.application.project.slug}-{release.application.slug}"
        )
        try:
            all_complete = True
            for process_name in release.processes:
                desired = deployment.application.process_counts.get(process_name, 0)
                if desired == 0:
                    continue
                if not deployment_is_complete(
                    apps_api_instance,
                    namespace,
                    release,
                    service_account_name,
                    process_name,
                ):
                    all_complete = False
                    break

            if all_complete:
                logger.info(
                    f"Completing stuck deployment {deployment.id} "
                    f"(rollout verified complete in K8s)"
                )
                deployment.complete = True
                if deployment.deploy_log:
                    deployment.deploy_log += (
                        "\nDeployment completed by stuck deployment reaper"
                    )
                else:
                    deployment.deploy_log = (
                        "Deployment completed by stuck deployment reaper"
                    )
                db.session.commit()

                if (
                    deployment.deploy_metadata
                    and "installation_id" in deployment.deploy_metadata
                    and "statuses_url" in deployment.deploy_metadata
                ):
                    from cabotage.server import github_app

                    access_token = github_app.fetch_installation_access_token(
                        deployment.deploy_metadata["installation_id"]
                    )
                    if access_token:
                        post_deployment_status_update(
                            access_token,
                            deployment.deploy_metadata["statuses_url"],
                            "success",
                            "Deployment complete!",
                        )
        except Exception:
            logger.exception(f"Error checking stuck deployment {deployment.id}")
