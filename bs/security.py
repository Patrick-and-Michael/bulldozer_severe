"""Writing custom decorators to control permissions."""
from flask import Flask, request, session, redirect, url_for, render_template, flash
from flask.ext.principal import AnonymousIdentity, Identity, identity_changed, Permission, Principal, RoleNeed
import os
from models import User, Usergroup
# from views import app

# class UsergroupOwnerPermission(Permission):
#     def __init__(self, id):
#         need = 

# class MemberPermission

# class QuestPermission


def user_match(user, matchable_class, id, property_name):
    """Compare a username to test membership in a object's property (list)."""
    def real_user_match(function):
        def wrapper(*args, **kwargs):
            property_list = getattr(matchable_class(id), property_name)
            success = user.username in property_list
            if success:
                function()
            else:
                flash("You don't have permission for that.")
                return redirect(request.fullpath)
        return wrapper
    return real_user_match
