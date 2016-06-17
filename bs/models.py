from py2neo import Graph, Node, Relationship, authenticate
from passlib.hash import bcrypt
import os


DATABASE_URL = os.environ.get('NEO4JDB')

url = os.environ.get(DATABASE_URL, 'http://localhost:7474')
username = os.environ.get('NEO4J_USERNAME')
password = os.environ.get('NEO4J_PASSWORD')

if username and password:
    authenticate(url.strip('http://'), username, password)

graph = Graph('{}/db/data/'.format(url))  # py2neo will raise 'Unauthorized'

class User(object):
    def __init__(self, username):
        self.username = username

    def get(self):
        user = graph.find_one("User", property_key="username", property_value=self.username)
        return user

    def register(self, password):
        if not self.get():
            user = Node("User", username=self.username, password=bcrypt.encrypt(password))
            graph.create(user)
            return True
        else:
            return False

    def verify_password(self,password):
        user = self.get()
        if user:
            return bcrypt.verify(password, user['password'])
        else:
            return False



