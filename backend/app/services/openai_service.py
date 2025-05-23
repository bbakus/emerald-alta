import os
import json
import requests
import time
import random
import base64
import uuid
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from ..models import Item, Inventory, Enemy, Move, NPC
from ..db import Session, session_scope
from flask_jwt_extended import create_access_token

# Load environment variables from .env file
load_dotenv()

class OpenAIService:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.image_api_url = "https://api.openai.com/v1/images/generations"
        
        # Check if API key is set
        if not self.api_key:
            print("WARNING: OPENAI_API_KEY environment variable is not set.")
            print("Please create a .env file in the backend directory with your OpenAI API key.")
            print("Example: OPENAI_API_KEY=your_key_here")
    
    def generate_response(self, messages, character=None, system_prompt=None):
        """
        Generate a response from OpenAI API based on chat history
        
        Args:
            messages: List of message dictionaries with 'content' and 'is_user' keys
            character: Character object with information about the player character
            system_prompt: Custom system prompt to override the default
            
        Returns:
            Response text from AI or error message
        """
        if not self.api_key:
            return "ERROR: OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable in the .env file."
        
        # Format chat history for OpenAI API
        formatted_messages = []
        
        # Add system prompt
        if not system_prompt:
            system_prompt = self._generate_system_prompt(character)
        
        # Add additional instruction for item giving
        system_prompt += "\n\nITEM GIVING: When you want to give an item to the player, describe it in the narrative, then add a special tag at the end of your message with the format: [ITEM:Name|Type|Effect Description]. The effect description should be a functional description of what the item does. When creating items, always make them interesting and thematic to Mesoamerican mythology and the game world. The item will be visualized as detailed 16-bit pixel art."
        
        # Add instruction for handling transactions
        system_prompt += "\n\nTRANSACTIONS: When the player purchases something, make sure to deduct the money from their wealth. Add a special tag with this format: [TRANSACTION:Amount|Description]. For example: [TRANSACTION:10|Purchase of leather boots]. Consider character's wealth before allowing expensive purchases."
        
        # Add instruction for combat damage
        system_prompt += "\n\nDAMAGE: When the character takes damage in combat or from environmental hazards, add a damage tag at the end of your message: [DAMAGE:Amount|Source]. For example: [DAMAGE:5|Goblin attack]. Similarly, for healing: [HEALING:Amount|Source]."
        
        # Add instruction for damage dealt by player
        system_prompt += "\n\nDAMAGE DEALT: When the character deals damage to enemies, ALWAYS add a damage dealt tag: [DAMAGE_DEALT:Amount|Target]. For example: [DAMAGE_DEALT:8|Goblin warrior]. Make sure to explicitly state all damage numbers in your narration."
        
        # Add instruction for MP usage
        system_prompt += "\n\nMANA USAGE: Whenever the character uses a spell, ability, or any action that consumes mana or magical energy, add a mana usage tag: [MP_USED:Amount|Source]. For example: [MP_USED:15|Fireball spell]. Make sure to track the character's MP and don't allow them to cast spells if they have insufficient MP."
        
        # Check if this is the first message (no chat history)
        is_first_message = len(messages) == 0 or (len(messages) == 1 and messages[0].get('is_user', True))
        
        if is_first_message:
            system_prompt += "\n\nThis is the first message in the conversation. Begin by describing the current setting in Mexico City where the character finds themselves. Create a vivid, detailed scene that establishes the mood, nearby landmarks, time of day, weather, and any supernatural phenomena that might be occurring. Then prompt the character to decide what they want to do next."
        
        formatted_messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Add chat history
        for msg in messages:
            role = "user" if msg.get('is_user', True) else "assistant"
            formatted_messages.append({
                "role": role,
                "content": msg.get('content', '')
            })
            
        # If there's no user message yet, add a default one
        if is_first_message and len(formatted_messages) == 1:  # Only system message
            formatted_messages.append({
                "role": "user",
                "content": "I'm ready to begin my adventure. Where do I find myself?"
            })
        
        # Initialize retry parameters
        max_retries = 3
        retry_count = 0
        base_delay = 1  # Base delay in seconds
        
        while retry_count <= max_retries:
            try:
                # Make request to OpenAI API
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                data = {
                    "model": "gpt-4",  # You can change this to other models like "gpt-3.5-turbo"
                    "messages": formatted_messages,
                    "temperature": 0.7,
                    "max_tokens": 500
                }
                
                print(f"Making request to OpenAI API (attempt {retry_count + 1}/{max_retries + 1})")
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    data=json.dumps(data)
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    ai_response = response_data['choices'][0]['message']['content']
                    
                    # Process entity creation and item giving if character exists
                    if character:
                        # Process all item tags until none are left
                        import re
                        item_pattern = r'\[ITEM:(.*?)\|(.*?)\|(.*?)\]'
                        while re.search(item_pattern, ai_response):
                            ai_response = self._process_item_giving(ai_response, character)
                        
                        # Process transactions
                        transaction_pattern = r'\[TRANSACTION:(.*?)\|(.*?)\]'
                        while re.search(transaction_pattern, ai_response):
                            ai_response = self._process_transaction(ai_response, character)
                        
                        # Process rewards
                        reward_pattern = r'\[REWARD:(.*?)\|(.*?)\]'
                        while re.search(reward_pattern, ai_response):
                            ai_response = self._process_reward(ai_response, character)
                        
                        # Process damage
                        ai_response = self._process_damage(ai_response, character)
                        
                        # Process enemy creation
                        ai_response = self._process_enemy_creation(ai_response, character)
                        
                        # Process NPC creation
                        ai_response = self._process_npc_creation(ai_response, character)
                    
                    return ai_response
                    
                elif response.status_code == 429:
                    # Rate limit hit, apply exponential backoff
                    if retry_count < max_retries:
                        retry_count += 1
                        # Calculate delay with jitter: 2^retry * base_delay + small random jitter
                        delay = (2 ** retry_count) * base_delay + random.uniform(0.1, 0.5)
                        print(f"Rate limit hit. Retrying in {delay:.2f} seconds...")
                        time.sleep(delay)
                        continue
                    else:
                        print(f"Rate limit error, max retries exceeded: {response.status_code}")
                        print(response.text)
                        return "I'm thinking too hard right now. Please try again in a moment."
                else:
                    print(f"Error from OpenAI API: {response.status_code}")
                    print(response.text)
                    return f"Error: Unable to generate response (HTTP {response.status_code})"
                    
            except Exception as e:
                print(f"Exception when calling OpenAI API: {str(e)}")
                
                # Only retry on network-related errors
                if isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
                    if retry_count < max_retries:
                        retry_count += 1
                        delay = (2 ** retry_count) * base_delay
                        print(f"Network error. Retrying in {delay:.2f} seconds...")
                        time.sleep(delay)
                        continue
                
                return f"Error: {str(e)}"
            
            # If we get here without continuing the loop, break out
            break
        
        return "Sorry, I'm having trouble responding right now. Please try again later."
    
    def _generate_system_prompt(self, character):
        """Generate a system prompt based on character information"""
        if not character:
            return "You are the dungeon master of a fantasy RPG game. Guide the player with immersive responses and creative prompts."

        prompt = f"""You are the Dungeon Master (DM) of *Emerald Altar*, a fantasy RPG set in 1920s Mexico City, blending Mesoamerican mythology, political unrest, and supernatural horror.

The player you are interacting with is {character.name}, a {character.race} {character.class_.name if hasattr(character, 'class_') and character.class_ else ''}.

Character Stats:
- Level: {int(character.exp / 100) + 1}
- Class: {character.class_.name if hasattr(character, 'class_') and character.class_ else 'Unknown'}
- HP: {character.hp_status}/{character.class_.hp if hasattr(character, 'class_') and character.class_ else 100}
- MP: {character.mp_status}/{character.class_.mp if hasattr(character, 'class_') and character.class_ else 100}
- Money: {character.money} pesos
- Background: {character.description if character.description else 'Unknown'}

WORLD SETTING:
Your first message should always set the scene with a vivid description of where the character finds themselves in Mexico City. The city is vast and true to its actual size, with distinct neighborhoods, landmarks, and supernatural hotspots. The metropolitan landscape is experiencing supernatural phenomena due to the cursed emerald being removed from its altar.

PRIMARY ANTAGONISTS:
The "Obsidian Circle" is a dark occult faction actively working to prevent the emerald from being returned to its altar. They believe the chaos and death unleashed by the curses will "purify" the world and usher in a new era of power. They are organized, dangerous, and have infiltrated various levels of society. Their agents include both humans and supernatural entities.

You are responsible for managing:
1. Combat encounters using D&D-style rules: Use d20 rolls for attacks and checks, and d4-d12 rolls for damage or effects.
2. Armor class checks: Determine whether attacks hit or miss based on the player's AC.
3. Status effects: Apply conditions like poisoned, cursed, or bleeding as needed.
4. Map generation: You can create new areas, dungeons, or landmarks and post them to the database for later reference.
5. Quest generation: Create multi-step quests with objectives, rewards, and narrative arcs, optionally posting them to the database.
6. NPC creation: Design characters with goals, backgrounds, and stats. They can assist or oppose the player and persist across sessions.
7. Item generation: Create usable, equipable, or lore-relevant items with names, descriptions, rarity, and stats. Each item will be visualized in high-quality 16-bit pixel art style with fine details, not simple 8-bit graphics.
8. Database awareness: You can refer back to any characters, quests, items, or maps previously generated or stored.
9. Story progression: You understand the overall plot of *Emerald Altar*, including the cursed emerald, spreading miasma, and citywide transformation.

COMBAT AND DAMAGE SYSTEM:
When in combat, calculate damage using these guidelines:
- Weak enemies: 1-4 damage per hit
- Standard enemies: 3-8 damage per hit
- Strong enemies: 6-12 damage per hit
- Boss enemies: 10-20 damage per hit

Always track all damage in the battle with these tag patterns:
- When a player takes damage: [DAMAGE:Amount|Source] (e.g., [DAMAGE:7|Cultist's dagger])
- When a player deals damage: [DAMAGE_DEALT:Amount|Target] (e.g., [DAMAGE_DEALT:12|Zombie cultist])
- When a player heals: [HEALING:Amount|Source] (e.g., [HEALING:10|Healing potion])

EXPLICITLY note all damage dealt to and by the player in your narration, then include the appropriate tag to update the character stats. 
Always report combat actions in detail, describing how much damage was dealt, by whom, and to whom.

MANA AND MP SYSTEM:
For spell casting and special abilities, track the MP cost:
- When a player uses MP: [MP_USED:Amount|Source] (e.g., [MP_USED:15|Fireball spell])
- Each class has different MP costs for their abilities
- Basic abilities cost 5-10 MP
- Intermediate abilities cost 15-25 MP
- Advanced abilities cost 30-50 MP

Always consider:
- Character's armor class for hit probability
- Character's attributes for damage modifiers
- Environmental factors that might increase or decrease damage
- Character's remaining MP for spell casting

If the player's HP reaches 0, they become unconscious but not dead. Make this clear in your narration.
If the player tries to use an ability with insufficient MP, inform them they cannot perform the action without enough magical energy.

ITEMS AND EQUIPMENT:
When creating items, be aware of these categories:
- Weapons: Swords, daggers, axes, bows, pistols, etc. for combat
- Armor: Protective gear that increases armor class
- Trinkets: Small magic items that provide minor bonuses
- Necklaces: Worn items that often provide magical benefits
- Helms: Headgear that can boost intelligence or wisdom
- Accessories: Rings, gloves, and other worn items
- Consumables: Potions, scrolls, or food items that are used once
- Key items: Items that pertain to quests, story line, reveal clues or are necessary for a later issue - for instance a puzzle that needs to be solved.

Items in the first six categories (weapons, armor, trinkets, necklaces, helms, accessories) are equippable. Players can equip them to gain their benefits. Equippable items should provide stat bonuses or special abilities.

SKILL CHECKS & ENCOUNTERS:
Frequently challenge the player with:
- Perception checks to notice hidden details, traps, or supernatural phenomena
- Wisdom checks to sense motives, resist manipulation, or commune with spirits
- Intelligence checks to decipher glyphs, understand occult rituals, or recall lore
- Surprise combat encounters that test the player's adaptability
- Moral dilemmas related to the Obsidian Circle's activities and victims

CREATING ENEMIES AND NPCS:
When you create a new enemy or NPC during the game, you should add them to the database by using special tags:

For enemies:
[ENEMY:Name|Description|Lore Description|HP|MP|AC|STR|DEX|SPD|WIS|INT|CON|CHA|INIT]

For enemy moves:
[ENEMY_MOVE:Name|Description|Lore Description|Damage|Mana Cost|Status Effect|Condition]

For NPCs:
[NPC:Name|Description|Lore Description|Role|Affiliation]

Place these tags at the end of your message, after describing the entity to the player in narrative form.

THEMES & STYLE:
- Evoke the atmosphere of post-revolutionary Mexico with mythic and supernatural elements.
- Avoid modern language or technology.
- Use rich, immersive language rooted in Mesoamerican imagery and folklore.
- You can describe the outcome of dice rolls and prompt the player to roll or continue.

FORMAT:
- Speak in-character as the DM.
- Offer player choices and actions when appropriate.
- Respond with clarity and tone that sustains immersion.

Your purpose is to facilitate an unforgettable RPG experience through dynamic, engaging narration and systems mastery."""
        return prompt
    
    def generate_quest(self, character=None, difficulty=None, quest_type=None):
        """
        Generate a quest based on character information
        
        Args:
            character: Character object with information about the player
            difficulty: Optional difficulty level (easy, medium, hard)
            quest_type: Optional quest type (combat, exploration, puzzle)
            
        Returns:
            Dictionary with quest data or error message
        """
        if not self.api_key:
            return {"error": "OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable in the .env file."}
        
        level = int(character.exp / 100) + 1 if character else 1
        difficulty = difficulty or "medium"
        quest_type = quest_type or "random"
        
        # Build prompt for quest generation
        prompt = f"""Generate a detailed quest for a level {level} character in a fantasy RPG game with Mesoamerican mythology theme.

Quest should be {difficulty} difficulty and focus on {quest_type if quest_type != "random" else "any type of"} gameplay.

OUTPUT FORMAT: Return a JSON object with the following fields:
- title: The name of the quest
- description: Detailed quest description (2-3 sentences)
- objectives: List of specific objectives for the quest
- reward_money: Amount of gold as reward (an integer)
- reward_item: Optional item reward with the following structure:
  - name: Name of the item
  - type: Type of item (weapon, armor, consumable, etc.)
  - description: Brief item description
  - rarity: Common, Uncommon, Rare, or Epic

DO NOT include any explanations, only provide valid JSON."""
        
        formatted_messages = [
            {
                "role": "system", 
                "content": "You are a quest generator for a fantasy RPG. Generate content in proper JSON format only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Initialize retry parameters
        max_retries = 3
        retry_count = 0
        base_delay = 1  # Base delay in seconds
        
        while retry_count <= max_retries:
            try:
                # Make request to OpenAI API
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                data = {
                    "model": "gpt-4",
                    "messages": formatted_messages,
                    "temperature": 0.7,
                    "max_tokens": 800,
                    "response_format": {"type": "json_object"}
                }
                
                print(f"Making quest generation request to OpenAI API (attempt {retry_count + 1}/{max_retries + 1})")
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    data=json.dumps(data)
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    quest_json = response_data['choices'][0]['message']['content']
                    return json.loads(quest_json)
                elif response.status_code == 429:
                    # Rate limit hit, apply exponential backoff
                    if retry_count < max_retries:
                        retry_count += 1
                        # Calculate delay with jitter: 2^retry * base_delay + small random jitter
                        delay = (2 ** retry_count) * base_delay + random.uniform(0.1, 0.5)
                        print(f"Rate limit hit. Retrying in {delay:.2f} seconds...")
                        time.sleep(delay)
                        continue
                    else:
                        print(f"Rate limit error, max retries exceeded: {response.status_code}")
                        print(response.text)
                        return {"error": "OpenAI rate limit reached. Please try again in a moment."}
                else:
                    print(f"Error from OpenAI API: {response.status_code}")
                    print(response.text)
                    return {"error": f"Unable to generate quest (HTTP {response.status_code})"}
                    
            except Exception as e:
                print(f"Exception when calling OpenAI API: {str(e)}")
                
                # Only retry on network-related errors
                if isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
                    if retry_count < max_retries:
                        retry_count += 1
                        delay = (2 ** retry_count) * base_delay
                        print(f"Network error. Retrying in {delay:.2f} seconds...")
                        time.sleep(delay)
                        continue
                
                return {"error": str(e)}
            
            # If we get here without continuing the loop, break out
            break
        
        return {"error": "Failed to generate quest after multiple attempts. Please try again later."}

    def _process_item_giving(self, ai_response, character):
        """Process item giving from AI response"""
        import re
        
        # Look for item tag pattern
        pattern = r'\[ITEM:(.*?)\|(.*?)\|(.*?)\]'
        match = re.search(pattern, ai_response)
        
        if match:
            # Extract item info
            item_name = match.group(1).strip()
            item_type = match.group(2).strip()
            item_description = match.group(3).strip()
            
            print(f"AI is suggesting item: {item_name} ({item_type}) - {item_description}")
            
            try:
                # Use session context manager
                with session_scope() as session:
                    # Check if an item with this name already exists in the database
                    existing_item = session.query(Item).filter(Item.name.ilike(f"%{item_name}%")).first()
                    
                    if existing_item:
                        print(f"Item with similar name '{existing_item.name}' already exists, using that")
                        item_id = existing_item.id
                    else:
                        # Create the new item
                        new_item = Item(
                            name=item_name,
                            type=item_type,
                            weight=1,  # Default weight
                            effect_description=item_description,
                            lore_description="An item found during your adventure.",
                            equippable=item_type in ["weapon", "armor", "shield", "helm", "accessory", "trinket", "necklace"],
                            is_equipped=False
                        )
                        
                        # Add stats based on type
                        if item_type == "weapon":
                            new_item.str = random.randint(1, 3)
                        elif item_type == "armor":
                            new_item.armor_class = random.randint(1, 3)
                        elif item_type == "shield":
                            new_item.armor_class = random.randint(1, 2)
                        elif item_type == "helm":
                            new_item.armor_class = 1
                            new_item.wisdom = random.randint(0, 1)
                        elif item_type == "accessory":
                            new_item.dex = random.randint(0, 2)
                        elif item_type == "trinket":
                            new_item.intelligence = random.randint(0, 2)
                        elif item_type == "necklace":
                            new_item.charisma = random.randint(0, 2)
                        
                        # Generate an image for the item
                        try:
                            image_path = self._generate_image(item_name, "item")
                            if image_path:
                                new_item.image_url = image_path
                        except Exception as img_err:
                            print(f"Error generating image for item: {str(img_err)}")
                        
                        # Add item to database and get its ID
                        session.add(new_item)
                        session.flush()  # Get ID without committing
                        item_id = new_item.id
                        
                        print(f"Successfully created item {item_name} in the database")
                    
                    # Instead of adding directly to inventory, add a note about being able to acquire it
                    # Remove the item tag and add a note that the item is available
                    ai_response = re.sub(pattern, f"\n\n(You can acquire the {item_name} if you'd like)", ai_response).strip()
                
            except Exception as e:
                print(f"Error processing item: {str(e)}")
                # Just remove the item tag without additional processing
                ai_response = re.sub(pattern, '', ai_response).strip()
        
        return ai_response
    
    def _generate_image(self, prompt, image_type="other"):
        """Internal method to generate an image using DALL-E
        
        Args:
            prompt: The text prompt to generate the image
            image_type: Type of image ("avatar", "item", or "other")
            
        Returns:
            Path to the saved image or None if generation failed
        """
        # Initialize retry parameters
        max_retries = 2
        retry_count = 0
        base_delay = 1
        
        # Add safety parameter and quality details
        safety_prompt = prompt + " High quality 16-bit pixel art with fine details, not 8-bit style. Avoid any content that may be considered inappropriate or offensive."
        
        while retry_count <= max_retries:
            try:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                # Try with DALL-E-3 first for high quality
                data = {
                    "model": "dall-e-3",
                    "prompt": safety_prompt,
                    "n": 1,
                    "size": "1024x1024",
                    "quality": "hd",
                    "response_format": "url"
                }
                
                print(f"Requesting image generation with DALL-E-3 (attempt {retry_count + 1}/{max_retries + 1})")
                response = requests.post(
                    self.image_api_url,
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    image_url = response_data['data'][0]['url']
                    
                    # Download the image
                    image_response = requests.get(image_url)
                    if image_response.status_code != 200:
                        print(f"Failed to download image from {image_url}")
                        return None
                        
                    # Create a unique filename
                    unique_id = uuid.uuid4().hex[:10]
                    if image_type == "avatar":
                        folder = "avatars"
                        filename = f"avatar_{unique_id}.png"
                    elif image_type == "item":
                        folder = "items"
                        filename = f"item_{unique_id}.png"
                    else:
                        folder = "other"
                        filename = f"image_{unique_id}.png"
                    
                    # Define path inside frontend public directory
                    images_dir = Path(f"../frontend/public/images/{folder}")
                    images_dir.mkdir(parents=True, exist_ok=True)
                    
                    image_path = images_dir / filename
                    
                    # Save the image
                    with open(image_path, 'wb') as f:
                        f.write(image_response.content)
                        
                    print(f"Image saved to {image_path}")
                    
                    # Return the URL path that will be accessible from frontend
                    return f"/images/{folder}/{filename}"
                    
                elif response.status_code == 429 or "model is currently overloaded" in str(response.text):
                    # Try with DALL-E-2 as fallback on rate limits or overload
                    data = {
                        "model": "dall-e-2",
                        "prompt": safety_prompt,
                        "n": 1,
                        "size": "1024x1024",
                        "response_format": "url"
                    }
                    
                    print(f"Requesting fallback image generation with DALL-E-2 (attempt {retry_count + 1}/{max_retries + 1})")
                    response = requests.post(
                        self.image_api_url,
                        headers=headers,
                        json=data
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        image_url = response_data['data'][0]['url']
                        
                        # Download the image
                        image_response = requests.get(image_url)
                        if image_response.status_code != 200:
                            print(f"Failed to download image from {image_url}")
                            return None
                            
                        # Create a unique filename
                        unique_id = uuid.uuid4().hex[:10]
                        if image_type == "avatar":
                            folder = "avatars"
                            filename = f"avatar_{unique_id}.png"
                        elif image_type == "item":
                            folder = "items"
                            filename = f"item_{unique_id}.png"
                        else:
                            folder = "other"
                            filename = f"image_{unique_id}.png"
                        
                        # Define path inside frontend public directory
                        images_dir = Path(f"../frontend/public/images/{folder}")
                        images_dir.mkdir(parents=True, exist_ok=True)
                        
                        image_path = images_dir / filename
                        
                        # Save the image
                        with open(image_path, 'wb') as f:
                            f.write(image_response.content)
                            
                        print(f"Image saved to {image_path}")
                        
                        # Return the URL path that will be accessible from frontend
                        return f"/images/{folder}/{filename}"
                        
                    elif response.status_code == 429:
                        # Rate limit hit, apply exponential backoff
                        if retry_count < max_retries:
                            retry_count += 1
                            delay = (2 ** retry_count) * base_delay + random.uniform(0.1, 0.5)
                            print(f"Rate limit hit. Retrying in {delay:.2f} seconds...")
                            time.sleep(delay)
                            continue
                        else:
                            print(f"Rate limit error, max retries exceeded: {response.status_code}")
                            print(response.text)
                            return None
                    else:
                        print(f"Error from OpenAI image API (fallback): {response.status_code}")
                        print(response.text)
                        return None
                else:
                    print(f"Error from OpenAI image API: {response.status_code}")
                    print(response.text)
                    return None
                    
            except Exception as e:
                print(f"Exception when calling OpenAI image API: {str(e)}")
                
                # Only retry on network-related errors
                if isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
                    if retry_count < max_retries:
                        retry_count += 1
                        delay = (2 ** retry_count) * base_delay
                        print(f"Network error. Retrying in {delay:.2f} seconds...")
                        time.sleep(delay)
                        continue
                
                return None
            
            # If we get here without continuing the loop, break out
            break
        
        return None
    
    def generate_character_avatar(self, character_name, character_class, character_description):
        """Generate a 16-bit style avatar image for a character using OpenAI's DALL-E model
        
        Args:
            character_name: Name of the character
            character_class: Class of the character (warrior, mage, etc.)
            character_description: Description of the character
            
        Returns:
            Path to the saved avatar image or None if generation failed
        """
        if not self.api_key:
            print("Cannot generate avatar: OpenAI API key not set")
            return None
            
        # Enhanced prompt for higher detail
        prompt = f"A highly detailed 16-bit pixel art portrait of a fantasy RPG character, {character_class}, with fine details and shading. High quality pixel art with detailed features, not 8-bit style. Character should have clear facial features and expressions with a dark fantasy atmospheric background. Include Mesoamerican elements in the design and setting. The background should be colorful and thematic, not blank or white."
        
        # Use the most minimal and reliable format for the API call
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": "dall-e-3",  # Use DALL-E 3 for higher quality
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024", 
            "quality": "hd"       # Request HD quality
        }
        
        try:
            print("Requesting character avatar generation...")
            response = requests.post(
                self.image_api_url,
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                response_data = response.json()
                image_url = response_data['data'][0]['url']
                
                # Download the image
                image_response = requests.get(image_url)
                if image_response.status_code != 200:
                    print(f"Failed to download avatar from {image_url}")
                    return None
                    
                # Create a unique filename
                filename = f"avatar_{uuid.uuid4().hex[:10]}_{character_name.replace(' ', '_').lower()}.png"
                
                # Define path inside frontend public directory
                images_dir = Path("../frontend/public/images/avatars")
                images_dir.mkdir(parents=True, exist_ok=True)
                
                image_path = images_dir / filename
                
                # Save the image
                with open(image_path, 'wb') as f:
                    f.write(image_response.content)
                    
                print(f"Avatar saved to {image_path}")
                
                # Return the URL path that will be accessible from frontend
                return f"/images/avatars/{filename}"
            else:
                print(f"Error from OpenAI image API: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"Exception when calling OpenAI image API: {str(e)}")
            return None
    
    def generate_character_bio(self, character_name, character_class):
        """Generate a character bio using OpenAI
        
        Args:
            character_name: Name of the character
            character_class: Class of the character
            
        Returns:
            Generated character biography or None if generation failed
        """
        if not self.api_key:
            print("Cannot generate bio: OpenAI API key not set")
            return None
        
        system_prompt = """You are a character backstory generator for a fantasy RPG set in 1920s Mexico City.
The game called Emerald Altar blends Mesoamerican mythology, political unrest, and supernatural horror.
Write a brief but compelling character backstory in 3-4 sentences maximum."""
        
        user_prompt = f"Create a backstory for {character_name}, a {character_class}. Make it mysterious and intriguing, with connections to Mesoamerican mythology and the supernatural."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            # Make request to OpenAI API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": "gpt-4",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 200
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return response_data['choices'][0]['message']['content']
            else:
                print(f"Error from OpenAI API: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"Exception when calling OpenAI API: {str(e)}")
            return None
    
    def _process_enemy_creation(self, ai_response, character):
        """Process enemy creation from AI response"""
        import re
        from ..models import Enemy, Move
        from ..db import Session
        
        # Look for enemy tag pattern
        enemy_pattern = r'\[ENEMY:(.*?)\|(.*?)\|(.*?)\|(.*?)\|(.*?)\|(.*?)\|(.*?)\|(.*?)\|(.*?)\|(.*?)\|(.*?)\|(.*?)\|(.*?)\|(.*?)\]'
        enemy_match = re.search(enemy_pattern, ai_response)
        
        if enemy_match:
            try:
                # Extract enemy info
                name = enemy_match.group(1).strip()
                description = enemy_match.group(2).strip()
                lore_description = enemy_match.group(3).strip()
                hp = int(enemy_match.group(4).strip())
                mp = int(enemy_match.group(5).strip())
                armor_class = int(enemy_match.group(6).strip())
                str_val = int(enemy_match.group(7).strip())
                dex = int(enemy_match.group(8).strip())
                speed = int(enemy_match.group(9).strip())
                wisdom = int(enemy_match.group(10).strip())
                intelligence = int(enemy_match.group(11).strip())
                constitution = int(enemy_match.group(12).strip())
                charisma = int(enemy_match.group(13).strip())
                initiative = int(enemy_match.group(14).strip())
                
                print(f"AI is creating enemy: {name}")
                
                # Create a database session
                session = Session()
                
                # Create the new enemy
                new_enemy = Enemy(
                    name=name,
                    description=description,
                    lore_description=lore_description,
                    hp=hp,
                    mp=mp,
                    armor_class=armor_class,
                    str=str_val,
                    dex=dex,
                    speed=speed,
                    wisdom=wisdom,
                    intelligence=intelligence,
                    constitution=constitution,
                    charisma=charisma,
                    initiative=initiative
                )
                
                # Add enemy to database
                session.add(new_enemy)
                session.commit()
                
                print(f"Successfully added enemy {name} to database")
                
                # Remove the enemy tag from the response
                ai_response = re.sub(enemy_pattern, '', ai_response).strip()
                
            except Exception as e:
                print(f"Error creating enemy: {str(e)}")
        
        # Process enemy moves
        move_pattern = r'\[ENEMY_MOVE:(.*?)\|(.*?)\|(.*?)\|(.*?)\|(.*?)\|(.*?)\|(.*?)\]'
        move_matches = re.finditer(move_pattern, ai_response)
        
        for match in move_matches:
            try:
                # Extract move info
                name = match.group(1).strip()
                description = match.group(2).strip()
                lore_description = match.group(3).strip()
                damage = int(match.group(4).strip())
                mana_cost = int(match.group(5).strip())
                status_effect = match.group(6).strip()
                condition = match.group(7).strip()
                
                print(f"AI is creating enemy move: {name}")
                
                # Create a database session
                session = Session()
                
                # Create the new move
                new_move = Move(
                    name=name,
                    description=description,
                    lore_description=lore_description,
                    damage=damage,
                    mana_cost=mana_cost,
                    status_effect=status_effect,
                    condition=condition
                )
                
                # Add move to database
                session.add(new_move)
                session.commit()
                
                print(f"Successfully added enemy move {name} to database")
                
            except Exception as e:
                print(f"Error creating enemy move: {str(e)}")
        
        # Remove all move tags from the response
        ai_response = re.sub(move_pattern, '', ai_response).strip()
        
        return ai_response
        
    def _process_npc_creation(self, ai_response, character):
        """Process NPC creation from AI response"""
        import re
        from ..models import NPC
        from ..db import Session
        
        # Look for NPC tag pattern
        npc_pattern = r'\[NPC:(.*?)\|(.*?)\|(.*?)\|(.*?)\|(.*?)\]'
        npc_match = re.search(npc_pattern, ai_response)
        
        if npc_match:
            try:
                # Extract NPC info
                name = npc_match.group(1).strip()
                description = npc_match.group(2).strip()
                lore_description = npc_match.group(3).strip()
                role = npc_match.group(4).strip()
                affiliation = npc_match.group(5).strip()
                
                print(f"AI is creating NPC: {name}")
                
                # Check if we have an NPC model
                try:
                    # Create a database session
                    session = Session()
                    
                    # Create the new NPC if the model exists
                    new_npc = NPC(
                        name=name,
                        description=description,
                        lore_description=lore_description,
                        role=role,
                        affiliation=affiliation
                    )
                    
                    # Add NPC to database
                    session.add(new_npc)
                    session.commit()
                    
                    print(f"Successfully added NPC {name} to database")
                    
                except Exception as e:
                    # If the NPC model doesn't exist, log it but don't fail
                    print(f"Warning: Could not add NPC to database. NPC model may not exist: {str(e)}")
                
                # Remove the NPC tag from the response
                ai_response = re.sub(npc_pattern, '', ai_response).strip()
                
            except Exception as e:
                print(f"Error creating NPC: {str(e)}")
        
        return ai_response

    def _process_transaction(self, ai_response, character):
        """Process monetary transactions from AI response"""
        import re
        
        # Look for transaction tag pattern
        pattern = r'\[TRANSACTION:(.*?)\|(.*?)\]'
        match = re.search(pattern, ai_response)
        
        if match:
            try:
                # Extract transaction info
                amount_str = match.group(1).strip()
                description = match.group(2).strip()
                
                # Convert amount to integer
                try:
                    amount = int(amount_str)
                except ValueError:
                    print(f"Invalid transaction amount: {amount_str}")
                    return ai_response
                
                print(f"Processing transaction: {description} for {amount} pesos")
                
                # Use session context manager
                with session_scope() as session:
                    # Get the current character from the database
                    current_character = session.query(character.__class__).filter_by(id=character.id).first()
                    
                    if not current_character:
                        print(f"Character not found in database: {character.id}")
                        return ai_response
                    
                    # Check if character has enough money
                    if current_character.money < amount:
                        print(f"Character does not have enough money: {current_character.money} < {amount}")
                        # Remove the transaction tag but don't process the transaction
                        ai_response = re.sub(pattern, '', ai_response).strip()
                        return ai_response
                    
                    # Deduct money from character
                    current_character.money -= amount
                    
                    # Try to extract item name from description if it's a purchase
                    # This helps avoid duplicate items in inventory
                    item_name = None
                    purchase_matches = re.search(r'Purchase of (.*?)$', description)
                    if purchase_matches:
                        item_name = purchase_matches.group(1).strip()
                        print(f"Detected item purchase: {item_name}")
                        
                        # Look for the item in the description to avoid duplicates
                        words = description.lower().split()
                        
                        # Check if character already has an item with a similar name
                        inventory_items = session.query(Inventory).filter_by(character_id=character.id).all()
                        for inv in inventory_items:
                            item = session.query(Item).filter_by(id=inv.item_id).first()
                            if item:
                                # Check if the item names are similar (case insensitive partial match)
                                if item_name.lower() in item.name.lower() or item.name.lower() in item_name.lower():
                                    print(f"Character already has similar item '{item.name}', skipping creation")
                                    # The session is committed automatically in session_scope
                                    # Remove the transaction tag from the response
                                    ai_response = re.sub(pattern, '', ai_response).strip()
                                    return ai_response
                
                # Session is automatically committed by the context manager
                print(f"Transaction successful. Character money reduced to {current_character.money}")
                
            except Exception as e:
                print(f"Error processing transaction: {str(e)}")
            
            # Remove the transaction tag from the response
            ai_response = re.sub(pattern, '', ai_response).strip()
        
        return ai_response

    def _process_reward(self, ai_response, character):
        """Process monetary rewards from AI response"""
        import re
        
        # Look for reward tag pattern
        pattern = r'\[REWARD:(.*?)\|(.*?)\]'
        match = re.search(pattern, ai_response)
        
        if match:
            try:
                # Extract reward info
                amount_str = match.group(1).strip()
                description = match.group(2).strip()
                
                # Convert amount to integer
                try:
                    amount = int(amount_str)
                except ValueError:
                    print(f"Invalid reward amount: {amount_str}")
                    return ai_response
                
                print(f"Processing reward: {description} for {amount} pesos")
                
                # Use session context manager
                with session_scope() as session:
                    # Get the current character from the database
                    current_character = session.query(character.__class__).filter_by(id=character.id).first()
                    
                    if not current_character:
                        print(f"Character not found in database: {character.id}")
                        return ai_response
                    
                    # Add money to character
                    current_character.money += amount
                    # Session is committed automatically in session_scope
                
                print(f"Reward successful. Character money increased to {current_character.money}")
                
            except Exception as e:
                print(f"Error processing reward: {str(e)}")
            
            # Remove the reward tag from the response
            ai_response = re.sub(pattern, '', ai_response).strip()
        
        return ai_response

    def _process_damage(self, ai_response, character):
        """Process damage or healing from AI response"""
        import re
        import requests
        
        # Look for damage tag pattern
        damage_pattern = r'\[DAMAGE:(.*?)\|(.*?)\]'
        damage_match = re.search(damage_pattern, ai_response)
        
        # Look for healing tag pattern
        healing_pattern = r'\[HEALING:(.*?)\|(.*?)\]'
        healing_match = re.search(healing_pattern, ai_response)
        
        # Look for MP usage pattern
        mp_pattern = r'\[MP_USED:(.*?)\|(.*?)\]'
        mp_match = re.search(mp_pattern, ai_response)
        
        # Look for damage dealt by player pattern
        damage_dealt_pattern = r'\[DAMAGE_DEALT:(.*?)\|(.*?)\]'
        damage_dealt_match = re.search(damage_dealt_pattern, ai_response)
        
        damage_amount = 0
        healing_amount = 0
        mp_amount = 0
        damage_dealt_amount = 0
        source = ""
        target = ""
        
        if damage_match:
            # Extract damage info
            try:
                damage_amount = int(damage_match.group(1).strip())
                source = damage_match.group(2).strip()
                
                print(f"AI is dealing {damage_amount} damage from {source}")
                
                # Remove the damage tag from the response
                ai_response = re.sub(damage_pattern, '', ai_response).strip()
                
            except ValueError:
                print(f"Invalid damage amount: {damage_match.group(1)}")
        
        if healing_match:
            # Extract healing info
            try:
                healing_amount = int(healing_match.group(1).strip())
                source = healing_match.group(2).strip()
                
                print(f"AI is healing for {healing_amount} from {source}")
                
                # Remove the healing tag from the response
                ai_response = re.sub(healing_pattern, '', ai_response).strip()
                
            except ValueError:
                print(f"Invalid healing amount: {healing_match.group(1)}")
                
        if mp_match:
            # Extract MP usage info
            try:
                mp_amount = int(mp_match.group(1).strip())
                mp_source = mp_match.group(2).strip()
                
                print(f"AI is using {mp_amount} MP for {mp_source}")
                
                # Remove the MP tag from the response
                ai_response = re.sub(mp_pattern, '', ai_response).strip()
                
            except ValueError:
                print(f"Invalid MP amount: {mp_match.group(1)}")
                
        if damage_dealt_match:
            # Extract damage dealt info
            try:
                damage_dealt_amount = int(damage_dealt_match.group(1).strip())
                target = damage_dealt_match.group(2).strip()
                
                print(f"Player dealt {damage_dealt_amount} damage to {target}")
                
                # Remove the damage dealt tag from the response
                ai_response = re.sub(damage_dealt_pattern, '', ai_response).strip()
                
            except ValueError:
                print(f"Invalid damage dealt amount: {damage_dealt_match.group(1)}")
        
        # If we have damage, healing, MP, or damage dealt to process
        if damage_amount > 0 or healing_amount > 0 or mp_amount > 0 or damage_dealt_amount > 0:
            try:
                # Get a valid token for the API request
                with session_scope() as session:
                    # Create a temporary token for the API call
                    token = create_access_token(identity=character.id)
                    
                    # Make a request to the API to update character's HP and MP
                    update_url = f"http://127.0.0.1:5000/api/characters/{character.id}/update-hp"
                    headers = {
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "Authorization": f"Bearer {token}"
                    }
                    
                    data = {
                        "damage": damage_amount,
                        "healing": healing_amount,
                        "mp_used": mp_amount,
                        "damage_dealt": damage_dealt_amount,
                        "source": source,
                        "target": target
                    }
                    
                    response = requests.post(
                        update_url,
                        headers=headers,
                        json=data
                    )
                
                if response.status_code == 200:
                    character_data = response.json()
                    print(f"HP/MP update successful, received updated character data")
                    
                    # Extract the damage info
                    damage_info = character_data.get('damage_info', {})
                    is_dead = damage_info.get('is_dead', False)
                    hp_status = damage_info.get('hp_status', 'unknown')
                    mp_status = damage_info.get('mp_status', 'unknown')
                    
                    # If character died, add a note to the response
                    if is_dead:
                        ai_response += "\n\n(Your health has reached 0. You are unconscious and require healing or rest to continue.)"
                    else:
                        # Add the HP/MP change to the response
                        response_notes = []
                        
                        # Report damage taken by player
                        if damage_amount > 0:
                            response_notes.append(f"You took {damage_amount} damage from {source}. Current HP: {hp_status}")
                        
                        # Report healing received by player
                        elif healing_amount > 0:
                            response_notes.append(f"You were healed for {healing_amount} from {source}. Current HP: {hp_status}")
                        
                        # Report MP used by player
                        if mp_amount > 0:
                            response_notes.append(f"You used {mp_amount} MP for {mp_source}. Current MP: {mp_status}")
                            
                        # Report damage dealt by player
                        if damage_dealt_amount > 0:
                            response_notes.append(f"You dealt {damage_dealt_amount} damage to {target}")
                            
                        if response_notes:
                            ai_response += "\n\n(" + ". ".join(response_notes) + ")"
                else:
                    print(f"Failed to update HP/MP: {response.status_code}")
                    print(response.text)
                    
            except Exception as e:
                print(f"Error updating character HP/MP: {str(e)}")
        
        return ai_response


# Initialize service
openai_service = OpenAIService()
