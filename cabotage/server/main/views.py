from urllib.parse import urljoin, urlparse

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_user

from cabotage.server.models.auth import User

main_blueprint = Blueprint(
    "main",
    __name__,
)


@main_blueprint.route("/_health/")
def health():
    return jsonify({"status": "ok"})


@main_blueprint.route("/")
def home():
    stats = {}
    if current_user.is_authenticated:
        projects = current_user.projects
        applications = []
        for p in projects:
            applications.extend(p.project_applications)
        deploy_count = 0
        for app in applications:
            deploy_count += app.deployments.count()
        stats = {
            "project_count": len(projects),
            "app_count": len(applications),
            "deploy_count": deploy_count,
        }
    return render_template("main/home.html", **stats)


@main_blueprint.route("/about/")
def about():
    return render_template("main/about.html")


def _is_safe_redirect_url(target):
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


@main_blueprint.route("/dev/quick-login")
def dev_quick_login():
    if not (current_app.debug or current_app.testing):
        abort(404)

    user = (
        User.query.filter_by(active=True)
        .order_by(User.admin.desc(), User.id.asc())
        .first()
    )
    if user is None:
        flash(
            "No active user found. Run cabotage/scripts/create_admin.py first.", "error"
        )
        return redirect(url_for("security.login"))

    login_user(user, remember=True)

    next_url = request.args.get("next")
    if _is_safe_redirect_url(next_url):
        return redirect(next_url)
    return redirect(url_for("main.home"))
