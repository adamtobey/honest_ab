import os

from honest_ab.factory import create_app
from honest_ab.database import db

application = create_app()

if __name__ == '__main__':
    application.run()
