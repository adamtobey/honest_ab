from honest_ab.models import User

def register_helpers(app):

    @app.context_processor
    def register_helper_functions():

        # Custom helper functions available in templates
        # define here

        def is_user(obj):
            return isinstance(obj, User)

        # register and name here
        return dict(
            is_user = is_user
        )
