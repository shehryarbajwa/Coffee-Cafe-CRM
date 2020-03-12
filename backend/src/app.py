import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    header['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, true'
    header['Access-Control-Allow-Methods'] = 'POST,GET,PUT,DELETE,PATCH,OPTIONS'
    return response

#db_drop_and_create_all()

## ROUTES

@app.route("/drinks")
def get_drinks():
    drinks = list(map(Drink.short, Drink.query.all()))
    result = {
        "success": True,
        "drinks": drinks
    }
    return jsonify(result)

@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_details(token):
        drinks = list(map(Drink.long, Drink.query.all()))
        result = {
            'success': True,
            'drinks': drinks
        }
        return jsonify(result)


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_drink(token):
    if request.data:
        body = request.get_json()
        title = body.get('title', None)
        recipe = body.get('recipe', None)
        drink = Drink(title=title, recipe=json.dumps(recipe))
        Drink.insert(drink)

        new_drink = Drink.query.filter_by(id=drink.id).first()

        return jsonify({
            'success': True,
            'drinks': [new_drink.long()]
        })
    else:
        abort(422)

@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drink(token, drink_id):
    data = request.get_json()
    title = data.get('title', None)
    recipe = data.get('recipe', None)

    try:
        drink = Drink.query.filter_by(id=drink_id).one_or_none()
        if drink is None:
            abort(404)

        if title is None:
            abort(400)
        
        if title is not None:
            drink.title = title

        if recipe is not None:
            drink.recipe = json.dumps(recipe)

        drink.update()

        updated_drink = Drink.query.filter_by(id=drink_id).first()

        return jsonify({
            'success': True,
            'drinks': [updated_drink.long()]
        })
    except:
        abort(422)


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(token, drink_id):
    try:
        drink = Drink.query.filter_by(id=drink_id).one_or_none()
        if drink is None:
            abort(404)
        drink.delete()
        return jsonify({
            'success': True,
            'deleted': drink_id
        })
    except:
        abort(422)



## Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    
    }), 404

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 401,
        'message': 'unauthorized'
    } , 401)

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': 405,
        'message': 'method not allowed'
    }, 405)

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        'success': False,
        'error': 500,
        'message': 'Internal Server Error'
    }, 500)

if __name__ == '__main__':
    app.run(port=8080, debug=True)
