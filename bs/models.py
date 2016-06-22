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
        user_node = graph.find_one("User",
                                   property_key="username",
                                   property_value=self.username)
        return user_node

    def register(self, password):
        if not self.get():
            user_node = Node("User",
                             username=self.username,
                             password=bcrypt.encrypt(password))
            graph.create(user_node)
            return True
        return False

    def verify_password(self, password):
        user = self.get()
        if user:
            return bcrypt.verify(password, user['password'])
        return False


class Usergroup(object):
    def __init__(self, groupname):
        """Instantiate a user group object."""
        self.groupname = groupname

    def get(self):
        """Return a usergroup node for given name."""
        usergroup_node = graph.find_one("Usergroup",
                                        property_key="groupname",
                                        property_value=self.groupname)
        return usergroup_node

    def register(self, user):
        """Register a user group, inserting a record into the db."""
        if not self.get():
            user_node = user.get()  # transform user object to user node object
            usergroup_node = Node("Usergroup", groupname=self.groupname)
            graph.create(usergroup_node)
            ownership = Relationship(user_node, 'owns', usergroup_node)
            graph.create(ownership)
            return usergroup_node
        return False
