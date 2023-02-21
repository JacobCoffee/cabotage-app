from celery import shared_task

from .build import (
    run_image_build,
    run_release_build,
)

from .deploy import (
    run_deploy,
)

from .github import (
    process_github_hook
)


@shared_task()
def is_this_thing_on():
    print('mic check!')
