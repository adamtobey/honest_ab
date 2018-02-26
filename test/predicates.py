def requires_authentication(response):
    on_login_form = b'id="full-login-form"' in response.data
    redirecting_to_login = response.status == '302 FOUND' and b"/users/login" in response.data

    return on_login_form or redirecting_to_login

def requires_app_key(response):
    return response.status_code == 403
