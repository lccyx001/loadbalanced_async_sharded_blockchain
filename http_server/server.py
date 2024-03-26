import os

from flask import Flask


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, )
    
    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0',port=5000,)