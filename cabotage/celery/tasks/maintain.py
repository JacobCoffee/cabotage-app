import datetime
import logging

import kubernetes

from celery import shared_task

from cabotage.server import kubernetes as kubernetes_ext

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
def recover_stuck_pipelines():
    from cabotage.celery.tasks.build import run_image_build, run_release_build
    from cabotage.celery.tasks.deploy import run_deploy
    from cabotage.server.models.projects import Deployment, Image, Release

    cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)

    stuck_images = Image.query.filter(
        Image.built.is_(False),
        Image.error.is_(False),
        Image.updated < cutoff,
    ).all()
    for image in stuck_images:
        logger.warning(
            "Recovering stuck image build %s (updated %s)",
            image.id,
            image.updated,
        )
        run_image_build.delay(image_id=image.id)

    stuck_releases = Release.query.filter(
        Release.built.is_(False),
        Release.error.is_(False),
        Release.updated < cutoff,
    ).all()
    for release in stuck_releases:
        logger.warning(
            "Recovering stuck release build %s (updated %s)",
            release.id,
            release.updated,
        )
        run_release_build.delay(release_id=release.id)

    stuck_deployments = Deployment.query.filter(
        Deployment.complete.is_(False),
        Deployment.error.is_(False),
        Deployment.updated < cutoff,
    ).all()
    for deployment in stuck_deployments:
        logger.warning(
            "Recovering stuck deployment %s (updated %s)",
            deployment.id,
            deployment.updated,
        )
        run_deploy.delay(deployment_id=deployment.id)
