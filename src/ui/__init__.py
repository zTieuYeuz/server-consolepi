"""Console Pi - cac tab giao dien moi (bo cuc thanh trai + noi dung phai)."""
from .layout import render_page, get_status_chips          # noqa: F401
from .auth import register_auth                            # noqa: F401
from .home import register_home                            # noqa: F401
from .terminal import register_terminal                    # noqa: F401
from .ssh import register_ssh                              # noqa: F401
from .commands import register_commands                    # noqa: F401
from .settings import register_settings                    # noqa: F401
from .docs import register_docs                            # noqa: F401
from .network import register_network                      # noqa: F401
from .storage import register_storage                      # noqa: F401
from .direct import register_direct                        # noqa: F401
from .remote import register_remote                        # noqa: F401
from .api import register_api                              # noqa: F401
from .logs import register_logs                            # noqa: F401


def register_all(app):
    """Gan toan bo tab moi vao app Flask (goi tu app.py)."""
    register_auth(app)
    register_home(app)
    register_terminal(app)
    register_ssh(app)
    register_commands(app)
    register_settings(app)
    register_docs(app)
    register_network(app)
    register_storage(app)
    register_direct(app)
    register_remote(app)
    register_api(app)
    register_logs(app)
    return app
