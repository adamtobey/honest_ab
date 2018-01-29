from honest_ab.models import User
from werkzeug.local import LocalProxy

def register_helpers(app):

    @app.context_processor
    def register_helper_functions():

        # Custom helper functions available in templates
        # define here

        def is_user(obj):
            if isinstance(obj, LocalProxy):
                obj = obj._get_current_object()
            return isinstance(obj, User)

        # register and name here
        return dict(
            is_user = is_user
        )
