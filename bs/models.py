"""This module contains models for bulldozer_severe."""
from datetime import datetime
from py2neo import Graph, Node, Relationship, authenticate
from passlib.hash import bcrypt
from uuid import uuid4
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
                             id=uuid4().hex,
                             password=bcrypt.encrypt(password))
            graph.create(user_node)
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
        user_node = self.get()
        grouplist = []
        if user_node:
            for rel in graph.match(start_node=user_node, rel_type='in'):
                grouplist.append(Usergroup(id=rel.end_node()['id']))
        return grouplist


class Usergroup(object):
    """Define a usergroup model."""

    def __init__(self, groupname=None, id=None, session=None):
        """Instantiate a user group object."""
        self.id = id
        if id:
            self.usergroup_node = Usergroup.get_by_id(self.id)
            self.groupname = self.usergroup_node['groupname']
        elif groupname and session:
            user = User(session['username'])
            user_node = user.get()
            for rel in graph.match(start_node=user_node, rel_type='in'):
                if rel.end_node()['groupname'] == groupname:
                    self.usergroup_node = rel.end_node()
                    self.id = self.usergroup_node['id']
                    break
            self.groupname = groupname
        elif groupname and not session:
            # TODO: get better error
            raise AttributeError('User needs to log in.')
        else:
            raise TypeError('Provide groupname or id or both.')

    @property
    def owners(self):
        """Return a list of current group owners."""
        return self.find_users_by_rel('owner')

    @property
    def members(self):
        """Return a list of current group members."""
        return self.find_users_by_rel('member')

    @classmethod
    def get_by_id(cls, id):
        """Return a usergroup_node by id lookup."""
        usergroup_node = graph.find_one('Usergroup',
                                        property_key='id',
                                        property_value=id)
        return usergroup_node

    def get(self):
        """Return a usergroup node for given id."""
        usergroup_node = graph.find_one("Usergroup",
                                        property_key='id',
                                        property_value=self.id)
        return usergroup_node

    def register(self, user):
        """Register a user group, inserting a record into the db."""
        if not self.get():
            user_node = user.get()  # transform user object to user node object
            usergroup_node = Node("Usergroup",
                                  groupname=self.groupname,
                                  id=uuid4().hex)
            graph.create(usergroup_node)
            ownership = Relationship(user_node, 'owns', usergroup_node)
            membership = Relationship(user_node, 'in', usergroup_node)
            graph.create(ownership)
            graph.create(membership)
            self.usergroup_node = usergroup_node
            self.id = usergroup_node['id']
            return usergroup_node
        return False

#     def get_by_id(self):
#         usergroup_node = graph.find_one("Usergroup",
#                                         property_key="id",
#                                         property_value=self.id)
#         return usergroup_node

    def add_member(self, user):
        """Add a 'in' relationship between a usergoup and a user."""
        user_in = user.get_groups()
        for group in user_in:
            if self.usergroup_node == group.usergroup_node:
                print('user is already a member')
                return False
        membership = Relationship(user.get(), 'in', self.usergroup_node)
        graph.create(membership)
        return self.usergroup_node

    def add_owner(self, user):
        """Make a user an owner of a usergroup."""
        user_in = user.get_groups()
        member = False
        for group in user_in:
            if self.usergroup_node == group.usergroup_node:
                member = True
        ownership = Relationship(user.get(), 'owns', self.usergroup_node)
        graph.create(ownership)
        if not member:
            membership = Relationship(user.get(), 'in', self.usergroup_node)
            graph.create(membership)
        return self.usergroup_node

    def find_users_by_rel(self, rel):
        """Return users by relation."""
        userlist = []
        for r in graph.match(end_node=self.usergroup_node, rel_type=rel):
            userlist.append(User(r.start_node()['username']))
        return userlist

class Quest(object):
    """Define a Quest model"""
    def __init__(self, group=None, id=None, session=None, questname=None):
        """Instantiate a quest object; requires (usergroup object and questname) or id."""
        self.id = id
        if id:
            self.quest_node = Quest.get_by_id(self.id)
            self.questname = self.quest_node['questname']
        elif group and questname:
            group_node = group.get()
            for rel in graph.match(start_node=group_node, rel_type='has_quest'):
                if rel.end_node()['questname'] == questname and rel.end_node()['active'] == True:
                    self.quest_node = rel.end_node()
                    self.id = self.quest_node['id']
                    break
        elif group and not questname:
            # TODO: get better error
            raise AttributeError('You must submit a questname with the group object.')
        else:
            raise TypeError('Provide quest id or usergroup object and questname or both.')
        if self.quest_node:
            self.questname = self.quest_node['questname']
            self.reward = self.quest_node['reward']
            self.active = self.quest_node['active']
            self.creator = self.quest_node['creator']

    def get(self):
        """Return a usergroup node for given id."""
        quest_node = graph.find_one("Quest",
                                        property_key='id',
                                        property_value=self.id)
        return usergroup_node

    def register(self, group, user, questname, reward):
        """Register a new quest - requires the usergroup, user, and reward objects and a questname string."""
        if not self.get():
            group_node = group.get()  # transform usergroup object to usergroup node object.
            user_node = user.get()  # ditto for the creating user.
            quest_node = Node("Quest",
                              questname=questname,
                              id=uuid4().hex),
                              created=datetime.now(),
                              reward=reward,
                              active=True,)
            graph.create(quest_node)
            created_by = Relationship(user_node, 'created', quest_node)
            has_quest = Relationship(group_node, 'has quest', quest_node)
            graph.create(created_by)
            graph.create(membership)
            self.quest_node = quest_node
            self.id = quest_node['id']
            self.creator = user
            self.reward = quest_node['reward']
            self.questname = quest_node['questname']
        return self

