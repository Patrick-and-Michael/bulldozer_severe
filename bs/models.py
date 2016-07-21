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
                             password=bcrypt.encrypt(password),
                             level=1,
                             xp=0,
                             gold=0,)
            graph.create(user_node)
        return self

    def get_by_id(self):
        """Look up node by ID and return the node."""
        user_node = graph.find_one("User",
                                   property_key="id",
                                   property_value=self.id)
        return user_node

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
        return self

#     def get_by_id(self):
#         usergroup_node = graph.find_one("Usergroup",
#                                         property_key="id",
#                                         property_value=self.id)
#         return usergroup_node

    def add_member(self, user):
        """Add an 'in' relationship between a usergoup and a user."""
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
    """Define a Quest model."""

    def __init__(self, group=None, id=None, session=None, questname=None):
        """Instantiate a quest object.

        Requires (usergroup object and questname) or id."""
        self.id = id
        if id:
            self.quest_node = Quest.get_by_id(self.id)
        elif group and questname:
            group_node = group.get()
            for rel in graph.match(start_node=group_node,
                                   rel_type='has_quest'):
                if rel.end_node()['questname'] == questname and \
                   rel.end_node()['active']:
                    self.quest_node = rel.end_node()
                    self.id = self.quest_node['id']
                    break
        elif group and not questname:
            # TODO: get better error
            raise AttributeError('You must submit a questname with the group '
                                 'object.')
        else:
            raise TypeError('Provide quest id or usergroup object and '
                            'questname or both.')
        try:
            self.questname = self.quest_node['questname']
            self.reward = self.quest_node['reward']
            self.v_reward = self.quest_node['v_reward']
            self.active = self.quest_node['active']
            self.creator = self.quest_node['creator']
            self.created = self.quest_node['created']
            self.completed_by = self.quest_node['completed_by']
            self.approved = self.quest_node['approved']
            self.description = self.quest_node['description']
        except(AttributeError):
            pass

    def get(self):
        """Return a usergroup node for given id."""
        quest_node = graph.find_one("Quest",
                                    property_key='id',
                                    property_value=self.id)
        return quest_node

    def register(self, group, user, questname, virtual_reward):
        """Register a new quest.

        Requires the usergroup, user, and reward objects and a questname
        string."""
        if not self.get():
            group_node = group.get()  # get node from object
            user_node = user.get()  # ditto
            time = datetime.now()
            timestring = time.strftime("%d%m%Y %H:%M:%S")
            quest_node = Node("Quest",
                              questname=questname,
                              id=uuid4().hex,
                              created=timestring,
                              reward=None,
                              completed_by=None,
                              active=True,
                              approved=False,
                              description=None,)
            graph.create(quest_node)
            created_by = Relationship(user_node, 'created', quest_node)
            has_quest = Relationship(group_node, 'has_quest', quest_node)
            graph.create(created_by)
            graph.create(has_quest)
            for key, value in virtual_reward.items():
                reward_node = Node("Reward",
                                   key,
                                   id=uuid4().hex,
                                   type=key,
                                   amount=value,)
                graph.create(reward_node)
                pays = Relationship(quest_node, 'pays', reward_node)
                graph.create(pays)
            self.quest_node = quest_node
            self.id = quest_node['id']
            self.creator = user
            edges = self.graph.match(start_node=self.quest_node,
                                     rel_type='pays')
            self.v_reward = [(p['type'],
                              p['value']) for e in edges for p in e.end_node]
            self.questname = quest_node['questname']
            self.completed_by = quest_node['completed_by']
            self.approved = quest_node['approved']
            self.reward = quest_node['reward']
            self.description = quest_node['description']
        return self

    def add_quester(self, user):
        """Make a user eligible to complete a quest."""
        user_node = user.get()
        for rel in graph.match(start_node=user_node, rel_type='can_complete'):
            if rel.end_node()['id'] == self.id:
                raise KeyError("user is already on this quest")
        if user == self.creator:
            raise TypeError("creators are not eligible for their own quests.")
        else:
            graph.create(Relationship(user_node,
                                      'can_complete',
                                      self.quest_node))
            return True

    def complete(self, user):
        """Change the completed_by attribute to match a user object."""
        user_node = user.get()
        if graph.match(start_node=user_node,
                       rel_type='can_complete',
                       end_node=self.quest_node):
            self.completed_by = user
            self.quest_node['completed_by'] = user
            self.active = False
            self.quest_node['active'] = False

    def approve(self):
        """Approve the completion of a quest."""
        self.approved = True
        self.quest_node['approved'] = True
        self.payout()

    def deny(self):
        """Deny quest approval, remove completed value and return to active."""
        self.quest_node['completed_by'] = None
        self.completed_by = None
        self.active = True
        self.quest_node['active'] = True

    def payout(self):
        """Pay the quest reward to a completing user."""
        user = self.completed_by
        user_node = user.get()
        for key, value in self.v_reward:
            user_node[key] += value

    def add_description(self, description):
        """Add a description attribute to a quest node."""
        self.quest_node['description'] = description
        self.description = description

    def add_reward(self, reward):
        """Update a reward attribute to a string describing a real reward."""
        self.quest_node['reward'] = reward
        self.reward = reward
