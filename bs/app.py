from flask import Flask
app = Flask(__name__)

@app.route('/')
def root_route():
    return 'this is the root route'

if __name__ == '__main__':
    app.run()
