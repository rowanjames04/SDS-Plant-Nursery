from functools import wraps
from flask import Blueprint, abort, render_template
from flask_login import current_user, login_required

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
)


def staff_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_staff:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/plants")
@staff_required
def plants():
    from models import Plant
    plants = Plant.query.order_by(Plant.common_name).all()
    return render_template("admin/plants.html", plants=plants)
