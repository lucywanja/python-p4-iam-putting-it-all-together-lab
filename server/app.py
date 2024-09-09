#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe


class Signup(Resource):
    def post(self):
        data = request.get_json()

        if 'username' in data and 'password' in data:
            user = User(
                username=data['username'],
                image_url=data.get('image_url'),
                bio=data.get('bio')
            )
            user.password_hash = data['password']
            
            try:
                db.session.add(user)
                db.session.commit()
                session['user_id'] = user.id
                return user.to_dict(), 201
            except IntegrityError:
                db.session.rollback()
                return {'message': 'Username already taken.'}, 422
        else:
            return {'message': 'Failed to create user.'}, 422


class CheckSession(Resource):
    def get(self):
        user = User.query.filter(User.id == session.get('user_id')).first()

        if user:
            return user.to_dict()
        else:
            return {}, 401
    

class Login(Resource):
    def post(self):
        data = request.get_json()

        user = User.query.filter_by(username=data.get('username')).first()

        if user and user.authenticate(data['password']):
            session['user_id'] = user.id
            return user.to_dict()
        else:
            return {}, 401
            

class Logout(Resource):
    def delete(self):  
        if 'user_id' in session and session['user_id'] is not None:
            session.pop('user_id', None)
            return {}, 204
        else:
            return {'message': 'No active session'}, 401
            
            

class RecipeIndex(Resource):
    def get(self):
        if 'user_id' in session and session['user_id'] is not None:
            user_id = session['user_id']
            recipes = Recipe.query.filter_by(user_id=user_id).all()
            return [recipe.to_dict() for recipe in recipes], 200
        else:
            return {'message': 'Unauthorized'}, 401
            
    
    def post(self):
        if 'user_id' in session:
            data = request.get_json()

            if 'title' in data and 'instructions' in data and 'minutes_to_complete' in data:
                if len(data['instructions']) >= 50:
                    recipe = Recipe(
                        title=data['title'],
                        instructions=data['instructions'],
                        minutes_to_complete=data['minutes_to_complete'],
                        user_id=session['user_id']
                    )

                    db.session.add(recipe)
                    db.session.commit()
                    return recipe.to_dict(), 201
                else:
                    return {'message': 'Instructions must be at least 50 characters long.'}, 422
            else:
                return {'message': 'Missing required fields.'}, 422
        else:
            return {'message': 'Unauthorized'}, 401
        

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)