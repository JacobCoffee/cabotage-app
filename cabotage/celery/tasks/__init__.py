from cabotage.server import celery

from .build import (
    run_image_build,
    run_release_build,
)

from .deploy import (
    run_deploy,
)


@celery.task()
def is_this_thing_on():
    print('mic check!')
