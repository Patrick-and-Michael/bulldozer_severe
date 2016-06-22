"""This module contains models for bulldozer_severe."""
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
    """Define user object and related methods."""

    def __init__(self, username):
        """Set username based upon parameter."""
        self.username = username

    def get(self):
        """Return a node object corresponding to the user."""
        user_node = graph.find_one("User",
                                   property_key="username",
                                   property_value=self.username)
        return user_node

    def register(self, password):
        """Create a node object corresponding to the user."""
        if not self.get():
            user_node = Node("User",
                             username=self.username,
                             password=bcrypt.encrypt(password))
            graph.create(user_node)
            query = """RETURN id({node})"""
            node_id = graph.run(query, node=self.get())
            self.id = node_id
            user_node['id'] = self.id
            user_node.push()
            return True
        return False

    def get_by_id(self):
        """Look up node by ID and return the node."""
        usergroup_node = graph.find_one("User",
                                        property_key="id",
                                        property_value=self.id)
        return usergroup_node

    def verify_password(self, password):
        """Validate the user's password, return false if validation fail."""
        user = self.get()
        if user:
            return bcrypt.verify(password, user['password'])
        return False

    def get_groups(self):
        """Return a list of Usergroup objects in which the User is a member."""
        user = self.get()
        grouplist = []
        for rel in graph.match(start_node=user.get(), rel_type='in'):
            grouplist.append(Usergroup(rel.end_node()['groupname']))
        return grouplist


class Usergroup(object):
    """Define a usergroup model."""

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
            membership = Relationship(user_node, 'in', usergroup_node)
            graph.create(ownership)
            graph.create(membership)
            query = """RETURN id({node})"""
            node_id = graph.run(query, node=self.get())
            self.id = node_id
            usergroup_node['id'] = self.id
            usergroup_node.push()

            return usergroup_node
        return False

    def get_by_id(self):
        usergroup_node = graph.find_one("Usergroup",
                                        property_key="id",
                                        property_value=self.id)
        return usergroup_node

    def add_member(self, user):
        """Add a 'in' relationship between a usergoup and a user."""
        group_node = self.get()
        user_in = user.get_groups()
        for group in user_in:
            if group_node == group.get():
                print('user is already a member')
                return False
        membership = Relationship(user.get(), 'in', group_node)
        graph.create(membership)
        return group_node

    def add_owner(self, user):
        """Make a user an owner of a usergroup."""
        group_node = self.get()
        user_in = user.get_groups()
        member = False
        for group in user_in:
            if group_node == group.get():
                member = True
        ownership = Relationship(user.get(), 'owns', group_node)
        graph.create(ownership)
        if not member:
            membership = Relationship(user.get(), 'in', group_node)
            graph.create(membership)
        return group_node
