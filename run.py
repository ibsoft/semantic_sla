import logging
from app import create_app, db
from app.config import Config


app = create_app()


if __name__ == "__main__" :
    app.run()
    

    
