from flask import Flask
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy import Column, Integer, Float, String, Boolean, ForeignKey, Table, JSON, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime



Base = declarative_base()

class_moves = Table(
    'class_moves', Base.metadata,
    Column('class_id', Integer, ForeignKey('classes.id')),
    Column('move_id', Integer, ForeignKey('moves.id'))
)

enemy_moves = Table(
    'enemy_moves', Base.metadata,
    Column('enemy_id', Integer, ForeignKey('enemies.id')),
    Column('move_id', Integer, ForeignKey('moves.id'))
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)

    character_id = Column(Integer, ForeignKey('characters.id'))
    character = relationship("Character")  # Remove backref to avoid circular reference

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)




class Character(Base):

    __tablename__ = 'characters'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    race = Column(String(50), nullable=False)
    exp = Column(Integer, default=0)
    money = Column(Integer, default=15)  # Set default to 15 pesos
    avatar_url = Column(String(200), nullable=False)
    poisoned = Column(Boolean, default=False)
    cursed = Column(Boolean, default=False)
    bleeding = Column(Boolean, default=False)
    hp_status = Column(Integer, default=100)
    mp_status = Column(Integer, default=100)
    description = Column(Text)

    # inventory_id and inventory relationship removed; defined via Inventory model
    class_id = Column(Integer, ForeignKey('classes.id'))

    # Relationships
    class_ = relationship("Class_", back_populates="characters", overlaps="class")
    inventory = relationship("Inventory", back_populates="character", cascade="all, delete-orphan", overlaps="inventories")
    quests = relationship("Quest", back_populates="character", cascade="all, delete-orphan")


class Class_(Base):

    __tablename__ = 'classes'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    hp = Column(Integer)
    mp = Column(Integer)
    armor_class = Column(Integer)
    str = Column(Integer)
    dex = Column(Integer)
    speed = Column(Integer)
    wisdom = Column(Integer)
    intelligence = Column(Integer)
    constitution = Column(Integer)
    charisma = Column(Integer)
    initiative = Column(Integer)
    passive = Column(String, nullable=False)
    description = Column(String)  # NEW: Lore or summary for AI

    characters = relationship("Character", back_populates="class_", overlaps="class")
    moves = relationship("Move", secondary="class_moves", backref="classes")


class Item(Base):

    __tablename__="items"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    weight = Column(Integer)
    effect_description = Column(String, nullable=False)  # RENAMED
    lore_description = Column(String)  # NEW: Flavor text for AI
    image_url = Column(String)  # NEW: URL to the generated 16-bit style image
    armor_class = Column(Integer)
    str = Column(Integer)
    dex = Column(Integer)
    speed = Column(Integer)
    wisdom = Column(Integer)
    intelligence = Column(Integer)
    constitution = Column(Integer)
    charisma = Column(Integer)
    initiative = Column(Integer)
    equippable = Column(Boolean)
    is_equipped = Column(Boolean)

    # inventories relationship removed or adjusted if needed for single-item relationship

class Inventory(Base):
    __tablename__="inventories"

    id = Column(Integer, primary_key=True)

    item_id = Column(Integer, ForeignKey('items.id'))
    item = relationship("Item", backref='inventories')

    character_id = Column(Integer, ForeignKey('characters.id'))
    character = relationship("Character", backref="inventories")


class Enemy(Base):

    __tablename__="enemies"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    lore_description = Column(String)  # NEW: Background context
    hp = Column(Integer)
    mp = Column(Integer)
    armor_class = Column(Integer)
    str = Column(Integer)
    dex = Column(Integer)
    speed = Column(Integer)
    wisdom = Column(Integer)
    intelligence = Column(Integer)
    constitution = Column(Integer)
    charisma = Column(Integer)
    initiative = Column(Integer)

    inventory_id = Column(Integer, ForeignKey('inventories.id'))
    moves = relationship("Move", secondary="enemy_moves", backref="enemies")


class Move(Base):
    __tablename__ = "moves"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    damage = Column(Integer)
    mana_cost = Column(Integer)
    status_effect = Column(String)  # e.g., 'poison', 'stun'
    condition = Column(String)      # condition under which move is used
    lore_description = Column(String)  # NEW: Flavor/lore summary


class Map(Base):
    __tablename__ = "maps"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    map_data = Column(JSON)  # Changed from JSONB to JSON
    image_url = Column(String)
    ai_generated = Column(Boolean, default=True)
    created_at = Column(String, default=datetime.utcnow)


class Quest(Base):
    __tablename__ = 'quests'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    completed = Column(Boolean, default=False)
    reward_money = Column(Integer, default=0)
    reward_item_id = Column(Integer, ForeignKey('items.id'), nullable=True)
    character_id = Column(Integer, ForeignKey('characters.id'), nullable=False)
    
    # Relationships
    character = relationship("Character", back_populates="quests")
    reward_item = relationship("Item")


class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_user = Column(Boolean, default=True)  # True if sent by user, False if from AI
    character_id = Column(Integer, ForeignKey('characters.id'), nullable=False)
    
    # Relationships
    character = relationship("Character")


class NPC(Base):
    __tablename__ = 'npcs'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    lore_description = Column(Text)
    role = Column(String(100))  # e.g., 'merchant', 'quest giver', 'ally'
    affiliation = Column(String(100))  # e.g., 'Obsidian Circle', 'Resistance', 'Independent'
    created_at = Column(DateTime, default=datetime.utcnow)

