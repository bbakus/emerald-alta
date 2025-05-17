from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from flask import request, abort
from flask_restful import Resource, reqparse
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from .models import User, Character, Class_, Item, Inventory, Enemy, Move, Quest, ChatMessage
from .db import Session, session_scope
from werkzeug.security import generate_password_hash, check_password_hash
from marshmallow import Schema, fields
from sqlalchemy.orm.exc import NoResultFound
from .services.openai_service import openai_service

router = APIRouter()

# Pydantic models for request/response
class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
# ===================
# Schema Definitions
# ===================

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    email = fields.Str(required=True)
    character_id = fields.Int(dump_only=True)

class ClassSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    hp = fields.Int()
    mp = fields.Int()
    armor_class = fields.Int()
    str = fields.Int()
    dex = fields.Int()
    speed = fields.Int()
    wisdom = fields.Int()
    intelligence = fields.Int()
    constitution = fields.Int()
    charisma = fields.Int()
    initiative = fields.Int()
    passive = fields.Str(required=True)
    description = fields.Str()
    strength = fields.Int()
    dexterity = fields.Int()
    moves = fields.List(fields.Nested(lambda: MoveSchema(exclude=("class_",))))

class CharacterSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    race = fields.Str(required=True)
    exp = fields.Int(required=True)
    avatar_url = fields.Str(required=True)
    poisoned = fields.Bool()
    cursed = fields.Bool()
    bleeding = fields.Bool()
    hp_status = fields.Int()
    mp_status = fields.Int()
    money = fields.Int()
    class_id = fields.Int(required=True)
    description = fields.Str()
    class_ = fields.Nested(ClassSchema, dump_only=True)

class ItemSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    type = fields.Str(required=True)
    weight = fields.Int()
    effect_description = fields.Str(required=True)
    lore_description = fields.Str()
    image_url = fields.Str()
    armor_class = fields.Int()
    str = fields.Int()
    dex = fields.Int()
    speed = fields.Int()
    wisdom = fields.Int()
    intelligence = fields.Int()
    constitution = fields.Int()
    charisma = fields.Int()
    initiative = fields.Int()
    equippable = fields.Bool()
    is_equipped = fields.Bool()

class InventorySchema(Schema):
    id = fields.Int(dump_only=True)
    item_id = fields.Int(required=True)
    character_id = fields.Int(required=True)

class EnemySchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    hp = fields.Int()
    mp = fields.Int()
    armor_class = fields.Int()
    str = fields.Int()
    dex = fields.Int()
    speed = fields.Int()
    wisdom = fields.Int()
    intelligence = fields.Int()
    constitution = fields.Int()
    charisma = fields.Int()
    initiative = fields.Int()

class MoveSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    damage = fields.Int()
    mana_cost = fields.Int()
    status_effect = fields.Str()
    condition = fields.Str()
    lore_description = fields.Str()
    class_ = fields.Nested(lambda: ClassSchema(exclude=("moves",)), dump_only=True)

class QuestSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    description = fields.Str(required=True)
    completed = fields.Bool()
    reward_money = fields.Int()
    reward_item_id = fields.Int()
    character_id = fields.Int(required=True)
    reward_item = fields.Nested(lambda: ItemSchema(exclude=("reward_quests",)), dump_only=True)

class ChatMessageSchema(Schema):
    id = fields.Int(dump_only=True)
    content = fields.Str(required=True)
    timestamp = fields.DateTime(dump_only=True)
    is_user = fields.Bool()
    character_id = fields.Int(required=True)

# Create schema instances
user_schema = UserSchema()
users_schema = UserSchema(many=True)
character_schema = CharacterSchema()
characters_schema = CharacterSchema(many=True)
class_schema = ClassSchema()
classes_schema = ClassSchema(many=True)
item_schema = ItemSchema()
items_schema = ItemSchema(many=True)
inventory_schema = InventorySchema()
inventories_schema = InventorySchema(many=True)
enemy_schema = EnemySchema()
enemies_schema = EnemySchema(many=True)
move_schema = MoveSchema()
moves_schema = MoveSchema(many=True)
quest_schema = QuestSchema()
quests_schema = QuestSchema(many=True)
chat_message_schema = ChatMessageSchema()
chat_messages_schema = ChatMessageSchema(many=True)

# ===================
# Resource Classes
# ===================

# Auth Resources
class UserRegistration(Resource):
    def post(self):
        data = request.get_json()
        session = Session()
        
        if session.query(User).filter_by(username=data['username']).first():
            return {'message': 'Username already exists'}, 400
            
        if session.query(User).filter_by(email=data['email']).first():
            return {'message': 'Email already exists'}, 400
            
        new_user = User(
            username=data['username'],
            email=data['email']
        )
        new_user.set_password(data['password'])
        
        session.add(new_user)
        session.commit()
        
        return {'message': 'User created successfully', 'user_id': new_user.id}, 201

class UserLogin(Resource):
    def post(self):
        try:
            data = request.get_json()
            if not data:
                return {'message': 'No JSON data received'}, 400
                
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return {'message': 'Missing username or password'}, 400
                
            session = Session()
            user = session.query(User).filter_by(username=username).first()
            
            if not user:
                return {'message': 'User not found'}, 401
                
            if not user.check_password(password):
                return {'message': 'Invalid credentials'}, 401
                
            access_token = create_access_token(identity=user.id)
            
            return {
                'access_token': access_token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }, 200
        except Exception as e:
            print(f"Login error: {str(e)}")
            return {'message': f'Server error: {str(e)}'}, 500

# User Resources
class UserResource(Resource):
    @jwt_required()
    def get(self, user_id):
        session = Session()
        user = session.query(User).filter_by(id=user_id).first()
        
        if not user:
            return {'message': 'User not found'}, 404
            
        return user_schema.dump(user), 200
    
    @jwt_required()
    def put(self, user_id):
        data = request.get_json()
        session = Session()
        user = session.query(User).filter_by(id=user_id).first()
        
        if not user:
            return {'message': 'User not found'}, 404
            
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'password' in data:
            user.set_password(data['password'])
            
        session.commit()
        return user_schema.dump(user), 200
    
    @jwt_required()
    def delete(self, user_id):
        session = Session()
        user = session.query(User).filter_by(id=user_id).first()
        
        if not user:
            return {'message': 'User not found'}, 404
            
        session.delete(user)
        session.commit()
        return {'message': 'User deleted'}, 200

class UserList(Resource):
    @jwt_required()
    def get(self):
        session = Session()
        users = session.query(User).all()
        return users_schema.dump(users), 200

class CurrentUser(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        session = Session()
        user = session.query(User).filter_by(id=user_id).first()
        
        if not user:
            return {'message': 'User not found'}, 404
            
        return user_schema.dump(user), 200

# Character Resources
class CharacterResource(Resource):
    @jwt_required()
    def get(self, character_id):
        try:
            session = Session()
            character = session.query(Character).filter_by(id=character_id).first()
            
            if not character:
                return {'message': 'Character not found'}, 404
            
            # Get character data including class
            character_data = character_schema.dump(character)
            
            # Check if character has a class
            if character.class_id:
                # Get class details
                class_ = session.query(Class_).filter_by(id=character.class_id).first()
                if class_:
                    class_data = class_schema.dump(class_)
                    
                    # Add moves to the class data
                    moves = class_.moves
                    class_data['moves'] = moves_schema.dump(moves)
                    
                    # Add complete class data to character
                    character_data['class_'] = class_data
            
            return character_data, 200
        except Exception as e:
            print(f"Error in CharacterResource.get: {str(e)}")
            return {'message': f'Server error: {str(e)}'}, 500
    
    @jwt_required()
    def put(self, character_id):
        data = request.get_json()
        session = Session()
        character = session.query(Character).filter_by(id=character_id).first()
        
        if not character:
            return {'message': 'Character not found'}, 404
            
        for key, value in data.items():
            if hasattr(character, key):
                setattr(character, key, value)
                
        session.commit()
        return character_schema.dump(character), 200
    
    @jwt_required()
    def delete(self, character_id):
        session = Session()
        character = session.query(Character).filter_by(id=character_id).first()
        
        if not character:
            return {'message': 'Character not found'}, 404
            
        session.delete(character)
        session.commit()
        return {'message': 'Character deleted'}, 200

class CharacterList(Resource):
    @jwt_required()
    def get(self):
        session = Session()
        characters = session.query(Character).all()
        return characters_schema.dump(characters), 200
    
    @jwt_required()
    def post(self):
        data = request.get_json()
        session = Session()
        
        new_character = Character(
            name=data['name'],
            race=data['race'],
            exp=data.get('exp', 0),
            avatar_url=data['avatar_url'],
            poisoned=data.get('poisoned', False),
            cursed=data.get('cursed', False),
            bleeding=data.get('bleeding', False),
            hp_status=data.get('hp_status', 100),
            mp_status=data.get('mp_status', 100),
            money=data.get('money', 15),  # Default to 15 pesos if not specified
            class_id=data['class_id'],
            description=data.get('description', '')
        )
        
        session.add(new_character)
        session.commit()
        
        # If this character is being created for a user
        if 'user_id' in data:
            user = session.query(User).filter_by(id=data['user_id']).first()
            if user:
                user.character_id = new_character.id
                session.commit()
        
        return character_schema.dump(new_character), 201

# Class Resources
class ClassResource(Resource):
    def get(self, class_id):
        try:
            session = Session()
            class_ = session.query(Class_).filter_by(id=class_id).first()
            
            if not class_:
                return {'message': 'Class not found'}, 404
            
            # Get class data including moves
            class_data = class_schema.dump(class_)
            
            # Add moves to the response
            moves = class_.moves
            class_data['moves'] = moves_schema.dump(moves)
            
            return class_data, 200
        except Exception as e:
            print(f"Error in ClassResource.get: {str(e)}")
            return {'message': f'Server error: {str(e)}'}, 500
    
    @jwt_required()
    def put(self, class_id):
        data = request.get_json()
        session = Session()
        class_ = session.query(Class_).filter_by(id=class_id).first()
        
        if not class_:
            return {'message': 'Class not found'}, 404
            
        for key, value in data.items():
            if hasattr(class_, key):
                setattr(class_, key, value)
                
        session.commit()
        return class_schema.dump(class_), 200
    
    @jwt_required()
    def delete(self, class_id):
        session = Session()
        class_ = session.query(Class_).filter_by(id=class_id).first()
        
        if not class_:
            return {'message': 'Class not found'}, 404
            
        session.delete(class_)
        session.commit()
        return {'message': 'Class deleted'}, 200

class ClassList(Resource):
    def get(self):
        session = Session()
        classes = session.query(Class_).all()
        return classes_schema.dump(classes), 200
    
    @jwt_required()
    def post(self):
        data = request.get_json()
        session = Session()
        
        new_class = Class_(
            name=data['name'],
            hp=data.get('hp', 0),
            mp=data.get('mp', 0),
            armor_class=data.get('armor_class', 0),
            str=data.get('str', 0),
            dex=data.get('dex', 0),
            speed=data.get('speed', 0),
            wisdom=data.get('wisdom', 0),
            intelligence=data.get('intelligence', 0),
            constitution=data.get('constitution', 0),
            charisma=data.get('charisma', 0),
            initiative=data.get('initiative', 0),
            passive=data['passive']
        )
        
        session.add(new_class)
        session.commit()
        
        return class_schema.dump(new_class), 201

# Item Resources
class ItemResource(Resource):
    def get(self, item_id):
        session = Session()
        item = session.query(Item).filter_by(id=item_id).first()
        
        if not item:
            return {'message': 'Item not found'}, 404
            
        return item_schema.dump(item), 200
    
    @jwt_required()
    def put(self, item_id):
        data = request.get_json()
        session = Session()
        item = session.query(Item).filter_by(id=item_id).first()
        
        if not item:
            return {'message': 'Item not found'}, 404
            
        for key, value in data.items():
            if hasattr(item, key):
                setattr(item, key, value)
                
        session.commit()
        return item_schema.dump(item), 200
    
    @jwt_required()
    def delete(self, item_id):
        session = Session()
        item = session.query(Item).filter_by(id=item_id).first()
        
        if not item:
            return {'message': 'Item not found'}, 404
            
        session.delete(item)
        session.commit()
        return {'message': 'Item deleted'}, 200

class ItemList(Resource):
    def get(self):
        session = Session()
        items = session.query(Item).all()
        return items_schema.dump(items), 200
    
    @jwt_required()
    def post(self):
        data = request.get_json()
        session = Session()
        
        new_item = Item(
            name=data['name'],
            type=data['type'],
            weight=data.get('weight', 0),
            effect_description=data['effect_description'],
            lore_description=data.get('lore_description', ''),
            image_url=data.get('image_url', ''),
            armor_class=data.get('armor_class'),
            str=data.get('str'),
            dex=data.get('dex'),
            speed=data.get('speed'),
            wisdom=data.get('wisdom'),
            intelligence=data.get('intelligence'),
            constitution=data.get('constitution'),
            charisma=data.get('charisma'),
            initiative=data.get('initiative'),
            equippable=data.get('equippable', False),
            is_equipped=data.get('is_equipped', False)
        )
        
        session.add(new_item)
        session.commit()
        
        return item_schema.dump(new_item), 201

# Inventory Resources
class InventoryResource(Resource):
    @jwt_required()
    def get(self, inventory_id):
        session = Session()
        inventory = session.query(Inventory).filter_by(id=inventory_id).first()
        
        if not inventory:
            return {'message': 'Inventory not found'}, 404
            
        return inventory_schema.dump(inventory), 200
    
    @jwt_required()
    def delete(self, inventory_id):
        session = Session()
        inventory = session.query(Inventory).filter_by(id=inventory_id).first()
        
        if not inventory:
            return {'message': 'Inventory not found'}, 404
            
        session.delete(inventory)
        session.commit()
        return {'message': 'Inventory deleted'}, 200

class InventoryList(Resource):
    @jwt_required()
    def get(self):
        session = Session()
        inventories = session.query(Inventory).all()
        return inventories_schema.dump(inventories), 200
    
    @jwt_required()
    def post(self):
        data = request.get_json()
        session = Session()
        
        new_inventory = Inventory(
            item_id=data['item_id'],
            character_id=data['character_id']
        )
        
        session.add(new_inventory)
        session.commit()
        
        return inventory_schema.dump(new_inventory), 201

class CharacterInventory(Resource):
    @jwt_required()
    def get(self, character_id):
        with session_scope() as session:
            character = session.query(Character).filter_by(id=character_id).first()
            if not character:
                return {'message': 'Character not found'}, 404
                
            inventories = session.query(Inventory).filter_by(character_id=character_id).all()
            items = []
            
            for inventory in inventories:
                item = session.query(Item).filter_by(id=inventory.item_id).first()
                if item:
                    item_data = item_schema.dump(item)
                    item_data['inventory_id'] = inventory.id
                    items.append(item_data)
            
            return items, 200

# Enemy Resources
class EnemyResource(Resource):
    def get(self, enemy_id):
        session = Session()
        enemy = session.query(Enemy).filter_by(id=enemy_id).first()
        
        if not enemy:
            return {'message': 'Enemy not found'}, 404
            
        return enemy_schema.dump(enemy), 200
    
    @jwt_required()
    def put(self, enemy_id):
        data = request.get_json()
        session = Session()
        enemy = session.query(Enemy).filter_by(id=enemy_id).first()
        
        if not enemy:
            return {'message': 'Enemy not found'}, 404
            
        for key, value in data.items():
            if hasattr(enemy, key):
                setattr(enemy, key, value)
                
        session.commit()
        return enemy_schema.dump(enemy), 200
    
    @jwt_required()
    def delete(self, enemy_id):
        session = Session()
        enemy = session.query(Enemy).filter_by(id=enemy_id).first()
        
        if not enemy:
            return {'message': 'Enemy not found'}, 404
            
        session.delete(enemy)
        session.commit()
        return {'message': 'Enemy deleted'}, 200

class EnemyList(Resource):
    def get(self):
        session = Session()
        enemies = session.query(Enemy).all()
        return enemies_schema.dump(enemies), 200
    
    @jwt_required()
    def post(self):
        data = request.get_json()
        session = Session()
        
        new_enemy = Enemy(
            name=data['name'],
            description=data['description'],
            hp=data.get('hp', 0),
            mp=data.get('mp', 0),
            armor_class=data.get('armor_class', 0),
            str=data.get('str', 0),
            dex=data.get('dex', 0),
            speed=data.get('speed', 0),
            wisdom=data.get('wisdom', 0),
            intelligence=data.get('intelligence', 0),
            constitution=data.get('constitution', 0),
            charisma=data.get('charisma', 0),
            initiative=data.get('initiative', 0)
        )
        
        session.add(new_enemy)
        session.commit()
        
        return enemy_schema.dump(new_enemy), 201

# Move Resources
class MoveResource(Resource):
    def get(self, move_id):
        session = Session()
        move = session.query(Move).filter_by(id=move_id).first()
        
        if not move:
            return {'message': 'Move not found'}, 404
            
        return move_schema.dump(move), 200
    
    @jwt_required()
    def put(self, move_id):
        data = request.get_json()
        session = Session()
        move = session.query(Move).filter_by(id=move_id).first()
        
        if not move:
            return {'message': 'Move not found'}, 404
            
        for key, value in data.items():
            if hasattr(move, key):
                setattr(move, key, value)
                
        session.commit()
        return move_schema.dump(move), 200
    
    @jwt_required()
    def delete(self, move_id):
        session = Session()
        move = session.query(Move).filter_by(id=move_id).first()
        
        if not move:
            return {'message': 'Move not found'}, 404
            
        session.delete(move)
        session.commit()
        return {'message': 'Move deleted'}, 200

class MoveList(Resource):
    def get(self):
        session = Session()
        moves = session.query(Move).all()
        return moves_schema.dump(moves), 200
    
    @jwt_required()
    def post(self):
        data = request.get_json()
        session = Session()
        
        new_move = Move(
            name=data['name'],
            description=data['description'],
            damage=data.get('damage', 0),
            mana_cost=data.get('mana_cost', 0),
            status_effect=data.get('status_effect'),
            condition=data.get('condition')
        )
        
        session.add(new_move)
        session.commit()
        
        return move_schema.dump(new_move), 201

class ClassMoves(Resource):
    def get(self, class_id):
        try:
            session = Session()
            class_ = session.query(Class_).filter_by(id=class_id).first()
            
            if not class_:
                return {'message': 'Class not found'}, 404
                
            moves = class_.moves
            return moves_schema.dump(moves), 200
        except Exception as e:
            print(f"Error in ClassMoves.get: {str(e)}")
            return {'message': f'Server error: {str(e)}'}, 500

class EnemyMoves(Resource):
    def get(self, enemy_id):
        session = Session()
        
        enemy = session.query(Enemy).filter_by(id=enemy_id).first()
        if not enemy:
            return {'message': 'Enemy not found'}, 404
            
        moves = enemy.moves
        return moves_schema.dump(moves), 200

# Quest Resources
class QuestResource(Resource):
    @jwt_required()
    def get(self, quest_id):
        session = Session()
        quest = session.query(Quest).filter_by(id=quest_id).first()
        
        if not quest:
            return {'message': 'Quest not found'}, 404
            
        return quest_schema.dump(quest), 200
    
    @jwt_required()
    def put(self, quest_id):
        data = request.get_json()
        session = Session()
        quest = session.query(Quest).filter_by(id=quest_id).first()
        
        if not quest:
            return {'message': 'Quest not found'}, 404
            
        for key, value in data.items():
            if hasattr(quest, key):
                setattr(quest, key, value)
                
        session.commit()
        return quest_schema.dump(quest), 200
    
    @jwt_required()
    def delete(self, quest_id):
        session = Session()
        quest = session.query(Quest).filter_by(id=quest_id).first()
        
        if not quest:
            return {'message': 'Quest not found'}, 404
            
        session.delete(quest)
        session.commit()
        return {'message': 'Quest deleted'}, 200

class QuestList(Resource):
    @jwt_required()
    def get(self):
        session = Session()
        quests = session.query(Quest).all()
        return quests_schema.dump(quests), 200
    
    @jwt_required()
    def post(self):
        try:
            data = request.get_json()
            session = Session()
            
            new_quest = Quest(
                title=data['title'],
                description=data['description'],
                completed=data.get('completed', False),
                reward_money=data.get('reward_money', 0),
                reward_item_id=data.get('reward_item_id'),
                character_id=data['character_id']
            )
            
            session.add(new_quest)
            session.commit()
            
            return quest_schema.dump(new_quest), 201
        except Exception as e:
            print(f"Error creating quest: {str(e)}")
            return {'message': f'Server error: {str(e)}'}, 500

class CharacterQuests(Resource):
    @jwt_required()
    def get(self, character_id):
        session = Session()
        
        character = session.query(Character).filter_by(id=character_id).first()
        if not character:
            return {'message': 'Character not found'}, 404
            
        quests = session.query(Quest).filter_by(character_id=character_id).all()
        return quests_schema.dump(quests), 200

# Chat Resources
class ChatMessageResource(Resource):
    @jwt_required()
    def get(self, message_id):
        session = Session()
        message = session.query(ChatMessage).filter_by(id=message_id).first()
        
        if not message:
            return {'message': 'Message not found'}, 404
            
        return chat_message_schema.dump(message), 200
    
    @jwt_required()
    def delete(self, message_id):
        session = Session()
        message = session.query(ChatMessage).filter_by(id=message_id).first()
        
        if not message:
            return {'message': 'Message not found'}, 404
            
        session.delete(message)
        session.commit()
        return {'message': 'Message deleted'}, 200

class ChatMessageList(Resource):
    @jwt_required()
    def post(self):
        try:
            data = request.get_json()
            session = Session()
            
            new_message = ChatMessage(
                content=data['content'],
                is_user=data.get('is_user', True),
                character_id=data['character_id']
            )
            
            session.add(new_message)
            session.commit()
            
            return chat_message_schema.dump(new_message), 201
        except Exception as e:
            print(f"Error creating message: {str(e)}")
            return {'message': f'Server error: {str(e)}'}, 500

class CharacterChatHistory(Resource):
    @jwt_required()
    def get(self, character_id):
        session = Session()
        
        character = session.query(Character).filter_by(id=character_id).first()
        if not character:
            return {'message': 'Character not found'}, 404
            
        messages = session.query(ChatMessage).filter_by(character_id=character_id).order_by(ChatMessage.timestamp).all()
        return chat_messages_schema.dump(messages), 200

# Add OpenAI API endpoints
class ChatCompletion(Resource):
    @jwt_required()
    def post(self):
        try:
            data = request.get_json()
            character_id = data.get('character_id')
            
            with session_scope() as session:
                character = None
                
                if character_id:
                    character = session.query(Character).filter_by(id=character_id).first()
                    if not character:
                        return {'message': 'Character not found'}, 404
                
                # Get chat history
                messages = []
                if character:
                    chat_messages = session.query(ChatMessage).filter_by(character_id=character_id).order_by(ChatMessage.timestamp).all()
                    messages = chat_messages_schema.dump(chat_messages)
                
                # Generate AI response
                ai_response = openai_service.generate_response(messages, character)
                
                # Save AI response to database
                if character:
                    new_message = ChatMessage(
                        content=ai_response,
                        is_user=False,
                        character_id=character_id
                    )
                    session.add(new_message)
                    
                    # Return the saved message
                    return chat_message_schema.dump(new_message), 201
                
                # If no character, just return the response
                return {'content': ai_response}, 200
                
        except Exception as e:
            print(f"Error generating AI response: {str(e)}")
            return {'message': f'Server error: {str(e)}'}, 500

class GenerateQuest(Resource):
    @jwt_required()
    def post(self):
        try:
            data = request.get_json()
            session = Session()
            
            character_id = data.get('character_id')
            character = None
            
            if character_id:
                character = session.query(Character).filter_by(id=character_id).first()
                if not character:
                    return {'message': 'Character not found'}, 404
            
            difficulty = data.get('difficulty', 'medium')
            quest_type = data.get('quest_type', 'random')
            
            # Generate quest
            quest_data = openai_service.generate_quest(character, difficulty, quest_type)
            
            # Check for errors
            if 'error' in quest_data:
                return {'message': quest_data['error']}, 500
            
            # Create item if reward includes an item
            reward_item_id = None
            if 'reward_item' in quest_data and quest_data['reward_item']:
                item_data = quest_data['reward_item']
                
                new_item = Item(
                    name=item_data['name'],
                    type=item_data['type'],
                    effect_description=item_data.get('description', ''),
                    weight=item_data.get('weight', 1)
                )
                
                session.add(new_item)
                session.flush()  # Get ID without committing
                reward_item_id = new_item.id
            
            # Create quest in database
            new_quest = Quest(
                title=quest_data['title'],
                description=quest_data['description'],
                completed=False,
                reward_money=quest_data.get('reward_money', 0),
                reward_item_id=reward_item_id,
                character_id=character_id
            )
            
            session.add(new_quest)
            session.commit()
            
            # Return the created quest
            quest_response = quest_schema.dump(new_quest)
            
            # Add objectives to response (not stored in database)
            if 'objectives' in quest_data:
                quest_response['objectives'] = quest_data['objectives']
            
            return quest_response, 201
            
        except Exception as e:
            print(f"Error generating quest: {str(e)}")
            return {'message': f'Server error: {str(e)}'}, 500

# Add a new route for AI to give items to characters
class GiveItemToCharacter(Resource):
    @jwt_required()
    def post(self):
        try:
            data = request.get_json()
            session = Session()
            
            character_id = data.get('character_id')
            if not character_id:
                return {'message': 'Character ID is required'}, 400
                
            character = session.query(Character).filter_by(id=character_id).first()
            if not character:
                return {'message': 'Character not found'}, 404
                
            # Create the new item
            new_item = Item(
                name=data.get('name', 'Mystery Item'),
                type=data.get('type', 'misc'),
                weight=data.get('weight', 1),
                effect_description=data.get('description', 'An item given by the AI.'),
                lore_description=data.get('lore_description', ''),
                armor_class=data.get('armor_class', 0),
                str=data.get('str', 0),
                dex=data.get('dex', 0),
                speed=data.get('speed', 0),
                wisdom=data.get('wisdom', 0),
                intelligence=data.get('intelligence', 0),
                constitution=data.get('constitution', 0),
                charisma=data.get('charisma', 0),
                initiative=data.get('initiative', 0),
                equippable=data.get('equippable', False),
                is_equipped=False
            )
            
            session.add(new_item)
            session.flush()  # Get the ID without committing
            
            # Add item to character's inventory
            new_inventory = Inventory(
                item_id=new_item.id,
                character_id=character_id
            )
            
            session.add(new_inventory)
            session.commit()
            
            return {'message': 'Item added to inventory', 'item_id': new_item.id}, 201
            
        except Exception as e:
            print(f"Error giving item to character: {str(e)}")
            return {'message': f'Error: {str(e)}'}, 500

# Generate a character avatar
class GenerateCharacterAvatar(Resource):
    @jwt_required()
    def post(self):
        try:
            data = request.get_json()
            
            # Get parameters
            character_name = data.get('character_name', '')
            character_class = data.get('character_class', '')
            character_description = data.get('character_description', '')
            
            if not character_name or not character_class:
                return {'message': 'Character name and class are required'}, 400
            
            # Generate avatar using OpenAI
            image_url = openai_service.generate_character_avatar(
                character_name, 
                character_class, 
                character_description
            )
            
            if not image_url:
                return {'message': 'Failed to generate avatar image'}, 500
                
            return {'image_url': image_url}, 200
            
        except Exception as e:
            print(f"Error generating character avatar: {str(e)}")
            return {'message': f'Error: {str(e)}'}, 500

# Generate a character bio
class GenerateCharacterBio(Resource):
    @jwt_required()
    def post(self):
        try:
            data = request.get_json()
            
            # Get parameters
            character_name = data.get('character_name', '')
            character_class = data.get('character_class', '')
            
            if not character_name or not character_class:
                return {'message': 'Character name and class are required'}, 400
            
            # Generate bio using OpenAI
            bio = openai_service.generate_character_bio(character_name, character_class)
            
            if not bio:
                return {'message': 'Failed to generate character bio'}, 500
                
            return {'bio': bio}, 200
            
        except Exception as e:
            print(f"Error generating character bio: {str(e)}")
            return {'message': f'Error: {str(e)}'}, 500

# Test endpoint for generating an item with an image
class TestGenerateItem(Resource):
    @jwt_required()
    def post(self):
        try:
            data = request.get_json()
            session = Session()
            
            character_id = data.get('character_id')
            if not character_id:
                return {'message': 'Character ID is required'}, 400
                
            character = session.query(Character).filter_by(id=character_id).first()
            if not character:
                return {'message': 'Character not found'}, 404
            
            # Test item data    
            item_name = data.get('name', 'Obsidian Mirror')
            item_type = data.get('type', 'trinket')
            item_description = data.get('description', 'A polished obsidian mirror that shows glimpses of the spirit realm. Increases wisdom and intuition.')
            
            # Create the new item
            new_item = Item(
                name=item_name,
                type=item_type,
                weight=1,  # Default weight
                effect_description=item_description,
                lore_description="A sacred artifact from ancient times that connects the mortal world to Xibalba.",
                armor_class=0,
                str=0,
                dex=0,
                speed=0,
                wisdom=2,
                intelligence=1,
                constitution=0,
                charisma=0,
                initiative=0,
                equippable=True if item_type in ["weapon", "armor", "necklace", "trinket", "helm", "accessory"] else False,
                is_equipped=False
            )
            
            # Generate image for the item
            try:
                image_url = openai_service.generate_item_image(item_name, item_type, item_description)
                if image_url:
                    new_item.image_url = image_url
            except Exception as img_err:
                print(f"Error generating image for item: {str(img_err)}")
            
            # Add item to database
            session.add(new_item)
            session.flush()  # Get the ID without committing
            
            # Add item to character's inventory
            new_inventory = Inventory(
                item_id=new_item.id,
                character_id=character_id
            )
            
            session.add(new_inventory)
            session.commit()
            
            # Return the created item
            item_data = item_schema.dump(new_item)
            item_data['inventory_id'] = new_inventory.id
            
            return item_data, 201
            
        except Exception as e:
            print(f"Error in test item generation: {str(e)}")
            return {'message': f'Error: {str(e)}'}, 500

# Equip or unequip an item
class EquipItem(Resource):
    @jwt_required()
    def post(self, item_id):
        try:
            print(f"\n\n------------------------------")
            print(f"Equip request received for item_id: {item_id}")
            
            # Debug the request
            print(f"Request data: {request.data}")
            print(f"Request json: {request.json if request.is_json else 'No JSON data'}")
            print(f"Request headers: {dict(request.headers)}")
            
            data = request.get_json() if request.is_json else {}
            character_id = data.get('character_id')
            
            print(f"Extracted character_id: {character_id}")
            
            if not character_id:
                print("No character_id provided")
                return {'message': 'Character ID is required'}, 400
                
            with session_scope() as session:
                # Verify character exists
                character = session.query(Character).filter_by(id=character_id).first()
                if not character:
                    print(f"Character not found: {character_id}")
                    return {'message': 'Character not found'}, 404
                    
                # Verify the item exists
                item = session.query(Item).filter_by(id=item_id).first()
                if not item:
                    print(f"Item not found: {item_id}")
                    return {'message': 'Item not found'}, 404
                    
                # Verify the character has this item in inventory
                inventory = session.query(Inventory).filter_by(character_id=character_id, item_id=item_id).first()
                if not inventory:
                    print(f"Item {item_id} not in character {character_id} inventory")
                    return {'message': 'Item not in character inventory'}, 404
                    
                # Verify the item is equippable
                if not item.equippable:
                    print(f"Item {item_id} is not equippable, marking it as equippable")
                    item.equippable = True
                    
                # Unequip any currently equipped items of the same type if equipping
                if not item.is_equipped:
                    print(f"Unequipping other items of type: {item.type}")
                    currently_equipped = session.query(Item).join(Inventory).filter(
                        Inventory.character_id == character_id,
                        Item.type == item.type,
                        Item.is_equipped == True
                    ).all()
                    
                    for equipped_item in currently_equipped:
                        print(f"Unequipping item: {equipped_item.id} ({equipped_item.name})")
                        equipped_item.is_equipped = False
                
                # Toggle the equipped status
                item.is_equipped = not item.is_equipped
                print(f"Item {item_id} is now {'equipped' if item.is_equipped else 'unequipped'}")
                
                # Return result after committing (session.commit happens automatically in the context manager)
                result = {
                    'message': f"Item {'equipped' if item.is_equipped else 'unequipped'} successfully",
                    'item_id': item.id,
                    'is_equipped': item.is_equipped
                }
                print(f"Returning result: {result}")
                print(f"------------------------------\n\n")
                return result, 200
                
        except Exception as e:
            print(f"Error equipping item: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'message': f'Error: {str(e)}'}, 500

# List equipped items
class CharacterEquipment(Resource):
    @jwt_required()
    def get(self, character_id):
        with session_scope() as session:
            character = session.query(Character).filter_by(id=character_id).first()
            if not character:
                return {'message': 'Character not found'}, 404
                
            # Get equipped items
            equipped_items = session.query(Item).join(Inventory).filter(
                Inventory.character_id == character_id,
                Item.is_equipped == True
            ).all()
            
            return items_schema.dump(equipped_items), 200

# ===================
# Route Registration
# ===================

def initialize_routes(api):
    # Auth routes
    api.add_resource(UserRegistration, '/api/register')
    api.add_resource(UserLogin, '/api/login')
    
    # User routes
    api.add_resource(UserResource, '/api/users/<int:user_id>')
    api.add_resource(UserList, '/api/users')
    api.add_resource(CurrentUser, '/api/me')
    
    # Character routes
    api.add_resource(CharacterResource, '/api/characters/<int:character_id>')
    api.add_resource(CharacterList, '/api/characters')
    
    # Class routes
    api.add_resource(ClassResource, '/api/classes/<int:class_id>')
    api.add_resource(ClassList, '/api/classes')
    api.add_resource(ClassMoves, '/api/classes/<int:class_id>/moves')
    
    # Item routes
    api.add_resource(ItemResource, '/api/items/<int:item_id>')
    api.add_resource(ItemList, '/api/items')
    
    # Inventory routes
    api.add_resource(InventoryResource, '/api/inventories/<int:inventory_id>')
    api.add_resource(InventoryList, '/api/inventories')
    api.add_resource(CharacterInventory, '/api/characters/<int:character_id>/inventory')
    api.add_resource(EquipItem, '/api/items/<int:item_id>/equip')
    api.add_resource(CharacterEquipment, '/api/characters/<int:character_id>/equipment')
    
    # Enemy routes
    api.add_resource(EnemyResource, '/api/enemies/<int:enemy_id>')
    api.add_resource(EnemyList, '/api/enemies')
    api.add_resource(EnemyMoves, '/api/enemies/<int:enemy_id>/moves')
    
    # Move routes
    api.add_resource(MoveResource, '/api/moves/<int:move_id>')
    api.add_resource(MoveList, '/api/moves')
    
    # Quest routes
    api.add_resource(QuestResource, '/api/quests/<int:quest_id>')
    api.add_resource(QuestList, '/api/quests')
    api.add_resource(CharacterQuests, '/api/characters/<int:character_id>/quests')
    
    # Chat routes
    api.add_resource(ChatMessageResource, '/api/chat/messages/<int:message_id>')
    api.add_resource(ChatMessageList, '/api/chat/messages')
    api.add_resource(CharacterChatHistory, '/api/characters/<int:character_id>/chat')
    api.add_resource(ChatCompletion, '/api/ai/chat')
    
    # OpenAI integration routes
    api.add_resource(GenerateQuest, '/api/generate-quest')
    api.add_resource(GiveItemToCharacter, '/api/give-item')
    api.add_resource(GenerateCharacterAvatar, '/api/generate-avatar')
    api.add_resource(GenerateCharacterBio, '/api/generate-bio')
    api.add_resource(TestGenerateItem, '/api/test-generate-item')
