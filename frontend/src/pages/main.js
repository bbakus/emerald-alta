import { useState, useEffect, useRef } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import '../styles/main.css';

function Main() {
  const [character, setCharacter] = useState(null);
  const [quests, setQuests] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [activeTab, setActiveTab] = useState('game');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [diceResult, setDiceResult] = useState(null);
  const [rollingDie, setRollingDie] = useState(null);
  const [isAiResponding, setIsAiResponding] = useState(false);
  const [inventoryItems, setInventoryItems] = useState([]);
  const [equippedItems, setEquippedItems] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [showItemModal, setShowItemModal] = useState(false);
  const chatEndRef = useRef(null);
  const { userId } = useParams();
  const navigate = useNavigate();
  
  
  const rollDice = (sides) => {
    setRollingDie(sides);
    
   
    setTimeout(() => {
      const result = Math.floor(Math.random() * sides) + 1;
      setDiceResult({ sides, result });
      setRollingDie(null);
      
     
      if (activeTab === 'game' && character) {
        sendDiceRollToChat(sides, result);
      }
    }, 800);
  };
  
  
  const sendDiceRollToChat = async (sides, result) => {
    if (!character) return;
    
    const rollMessage = `🎲 I rolled a d${sides} and got ${result}`;
    
    
    const diceRollMessage = {
      content: rollMessage,
      is_user: true,
      timestamp: new Date().toISOString()
    };
    
    setChatMessages(prev => [...prev, diceRollMessage]);
    
    try {
      const token = localStorage.getItem('token');
      
      
      const response = await fetch('http://127.0.0.1:5000/api/chat/messages', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          content: rollMessage,
          is_user: true,
          character_id: character.id
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to send dice roll');
      }
      
      
      setIsAiResponding(true);
      
      
      const aiResponse = await fetch('http://127.0.0.1:5000/api/ai/chat', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          character_id: character.id
        })
      });
      
      if (aiResponse.ok) {
        
        const chatHistoryResponse = await fetch(`http://127.0.0.1:5000/api/characters/${character.id}/chat`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'application/json'
          }
        });
        
        if (chatHistoryResponse.ok) {
          const chatData = await chatHistoryResponse.json();
          setChatMessages(chatData);
        }
      } else {
        console.error('Failed to get AI response for dice roll:', aiResponse.status);
        
        
        if (aiResponse.status === 429) {
          
          const rateLimitMessage = {
            content: "The AI is currently experiencing high demand. Please wait a moment before sending another message.",
            is_user: false,
            timestamp: new Date().toISOString()
          };
          setChatMessages(prev => [...prev, rateLimitMessage]);
        } else {
          
          const errorMessage = {
            content: "I'm having trouble responding to your dice roll right now. Please try again in a moment.",
            is_user: false,
            timestamp: new Date().toISOString()
          };
          setChatMessages(prev => [...prev, errorMessage]);
        }
      }
    } catch (err) {
      console.error('Error sending dice roll to chat:', err);
      
      const errorMessage = {
        content: "There was an error processing your dice roll. Please try again.",
        is_user: false,
        timestamp: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsAiResponding(false);
    }
  };
  
  
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages]);

  
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const token = localStorage.getItem('token');
        
       
        console.log('Token from localStorage:', token);
        
        if (!token) {
          throw new Error('No authentication token found');
        }
        
        
        const response = await fetch(`http://127.0.0.1:5000/api/users/${userId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'application/json'
          }
        });
        
        console.log('User data response status:', response.status);
        
        if (!response.ok) {
          if (response.status === 401) {
            
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            throw new Error('Authentication expired. Please log in again.');
          }
          throw new Error('Failed to fetch user data');
        }
        
        const userData = await response.json();
        console.log('User data:', userData);
        
        
        if (userData.character_id) {
          // Fetch character details
          const characterResponse = await fetch(`http://127.0.0.1:5000/api/characters/${userData.character_id}`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Accept': 'application/json'
            }
          });
          
          if (!characterResponse.ok) {
            throw new Error('Failed to fetch character data');
          }
          
          const characterData = await characterResponse.json();
          console.log('Character data:', characterData);
          
          // If class_id exists but class_ data doesn't have moves, fetch them separately
          if (characterData.class_id && (!characterData.class_ || !characterData.class_.moves)) {
            const movesResponse = await fetch(`http://127.0.0.1:5000/api/classes/${characterData.class_id}/moves`, {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Accept': 'application/json'
              }
            });
            
            if (movesResponse.ok) {
              const movesData = await movesResponse.json();
              console.log('Class moves:', movesData);
              
              // Ensure class_ object exists
              if (!characterData.class_) {
                // If not, we need to fetch the class details too
                const classResponse = await fetch(`http://127.0.0.1:5000/api/classes/${characterData.class_id}`, {
                  headers: {
                    'Authorization': `Bearer ${token}`,
                    'Accept': 'application/json'
                  }
                });
                
                if (classResponse.ok) {
                  const classData = await classResponse.json();
                  console.log('Class data:', classData);
                  characterData.class_ = classData;
                }
              }
              
              // Add moves to character's class
              if (characterData.class_) {
                characterData.class_.moves = movesData;
              }
            }
          }
          
          setCharacter(characterData);
          
          // Fetch quests
          try {
            const questsResponse = await fetch(`http://127.0.0.1:5000/api/characters/${userData.character_id}/quests`, {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Accept': 'application/json'
              }
            });
            
            if (questsResponse.ok) {
              const questsData = await questsResponse.json();
              console.log('Quests data:', questsData);
              setQuests(questsData);
            }
          } catch (err) {
            console.error('Error fetching quests:', err);
          }
          
          // Fetch chat history
          try {
            const chatResponse = await fetch(`http://127.0.0.1:5000/api/characters/${userData.character_id}/chat`, {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Accept': 'application/json'
              }
            });
            
            if (chatResponse.ok) {
              const chatData = await chatResponse.json();
              console.log('Chat data:', chatData);
              setChatMessages(chatData);
            }
          } catch (err) {
            console.error('Error fetching chat history:', err);
          }
          
          // Fetch inventory items
          try {
            const inventoryResponse = await fetch(`http://127.0.0.1:5000/api/characters/${userData.character_id}/inventory`, {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Accept': 'application/json'
              }
            });
            
            if (inventoryResponse.ok) {
              const inventoryData = await inventoryResponse.json();
              console.log('Inventory data:', inventoryData);
              setInventoryItems(inventoryData);
            }

            // Also fetch equipped items
            const equipmentResponse = await fetch(`http://127.0.0.1:5000/api/characters/${userData.character_id}/equipment`, {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Accept': 'application/json'
              }
            });
            
            if (equipmentResponse.ok) {
              const equipmentData = await equipmentResponse.json();
              console.log('Equipment data:', equipmentData);
              setEquippedItems(equipmentData);
            }
          } catch (err) {
            console.error('Error fetching inventory or equipment:', err);
          }
        } else {
          // User has no character
          setCharacter(null);
        }
      } catch (err) {
        console.error('Error fetching user data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [userId]);
  
  // Handle chat submission
  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || !character) return;
    
    // Add user message to the chat
    const userMessage = {
      content: chatInput,
      is_user: true,
      timestamp: new Date().toISOString()
    };
    
    setChatMessages(prev => [...prev, userMessage]);
    
    try {
      const token = localStorage.getItem('token');
      
      // Send message to backend
      const response = await fetch('http://127.0.0.1:5000/api/chat/messages', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          content: chatInput,
          is_user: true,
          character_id: character.id
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to send message');
      }
      
      setChatInput('');
      
      // Show AI is responding
      setIsAiResponding(true);
      
      // Get AI response
      const aiResponse = await fetch('http://127.0.0.1:5000/api/ai/chat', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          character_id: character.id
        })
      });
      
      if (aiResponse.ok) {
        const aiData = await aiResponse.json();
        // AI message will be added to chat history, refresh chat messages
        const chatHistoryResponse = await fetch(`http://127.0.0.1:5000/api/characters/${character.id}/chat`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'application/json'
          }
        });
        
        if (chatHistoryResponse.ok) {
          const chatData = await chatHistoryResponse.json();
          setChatMessages(chatData);
        }
      } else {
        console.error('Failed to get AI response:', aiResponse.status);
        
        // Add a system message to inform the user about rate limiting
        if (aiResponse.status === 429) {
          // Add a rate limit message
          const rateLimitMessage = {
            content: "The AI is currently experiencing high demand. Please wait a moment before sending another message.",
            is_user: false,
            timestamp: new Date().toISOString()
          };
          setChatMessages(prev => [...prev, rateLimitMessage]);
        } else {
          // Add a generic error message
          const errorMessage = {
            content: "I'm having trouble responding right now. Please try again in a moment.",
            is_user: false,
            timestamp: new Date().toISOString()
          };
          setChatMessages(prev => [...prev, errorMessage]);
        }
      }
      
    } catch (err) {
      console.error('Error sending message:', err);
      // Add error message to chat
      const errorMessage = {
        content: "There was an error sending your message. Please try again.",
        is_user: false,
        timestamp: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsAiResponding(false);
    }
  };
  
  const handleLogout = () => {
    // Clear localStorage
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    
    // Redirect to landing page
    navigate('/');
  };

  // Handle item click to show details
  const handleItemClick = (item) => {
    setSelectedItem(item);
    setShowItemModal(true);
  };

  // Close item modal
  const handleCloseModal = () => {
    setShowItemModal(false);
    setSelectedItem(null);
  };

  // Add the handleEquipItem function
  const handleEquipItem = async () => {
    if (!selectedItem || !character) {
      console.error("Cannot equip: No selected item or character");
      return;
    }
    
    console.log("Equipping item:", selectedItem);
    console.log("Character ID:", character.id);
    
    try {
      const token = localStorage.getItem('token');
      console.log("Using token:", token ? "Token exists" : "No token found");
      
      const response = await fetch(`http://127.0.0.1:5000/api/items/${selectedItem.id}/equip`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          character_id: character.id
        })
      });
      
      console.log("Equip response status:", response.status);
      
      if (response.ok) {
        const result = await response.json();
        console.log('Equip result:', result);
        
        // Update the selected item
        setSelectedItem({
          ...selectedItem,
          is_equipped: result.is_equipped
        });
        
        // Refresh inventory and equipment lists
        const token = localStorage.getItem('token');
        
        const inventoryResponse = await fetch(`http://127.0.0.1:5000/api/characters/${character.id}/inventory`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'application/json'
          }
        });
        
        if (inventoryResponse.ok) {
          const inventoryData = await inventoryResponse.json();
          setInventoryItems(inventoryData);
        }
        
        const equipmentResponse = await fetch(`http://127.0.0.1:5000/api/characters/${character.id}/equipment`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'application/json'
          }
        });
        
        if (equipmentResponse.ok) {
          const equipmentData = await equipmentResponse.json();
          setEquippedItems(equipmentData);
        }
      } else {
        console.error('Failed to equip item:', response.status);
        // Try to get the error message from the response
        try {
          const errorData = await response.json();
          console.error('Error details:', errorData);
        } catch (err) {
          console.error('Could not parse error response');
        }
      }
    } catch (err) {
      console.error('Error equipping item:', err);
    }
  };

  // Add function to handle equipping items directly from inventory list
  const handleEquipItemFromList = async (e, item) => {
    e.stopPropagation(); // Prevent opening the modal
    if (!item || !character) return;
    
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch(`http://127.0.0.1:5000/api/items/${item.id}/equip`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          character_id: character.id
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('Equip result:', result);
        
        // Refresh inventory and equipment lists
        const inventoryResponse = await fetch(`http://127.0.0.1:5000/api/characters/${character.id}/inventory`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'application/json'
          }
        });
        
        if (inventoryResponse.ok) {
          const inventoryData = await inventoryResponse.json();
          setInventoryItems(inventoryData);
        }
        
        const equipmentResponse = await fetch(`http://127.0.0.1:5000/api/characters/${character.id}/equipment`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'application/json'
          }
        });
        
        if (equipmentResponse.ok) {
          const equipmentData = await equipmentResponse.json();
          setEquippedItems(equipmentData);
        }
      } else {
        console.error('Failed to equip item:', response.status);
      }
    } catch (err) {
      console.error('Error equipping item:', err);
    }
  };

  // Render tabs content
  const renderTabContent = () => {
    switch (activeTab) {
      case 'game':
        return (
          <div className="chat-interface">
            <h4>Game Chat</h4>
            <div className="chat-messages">
              {chatMessages.map((msg, index) => (
                <div 
                  key={index} 
                  className={`chat-message ${msg.is_user ? 'user-message' : 'ai-message'}`}
                >
                  <div className="message-content">{msg.content}</div>
                  <div className="message-timestamp">
                    {new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  </div>
                </div>
              ))}
              {isAiResponding && (
                <div className="ai-typing">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
            <form className="chat-input-form" onSubmit={handleChatSubmit}>
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Type your message..."
                disabled={!character || isAiResponding}
              />
              <button type="submit" disabled={!character || !chatInput.trim() || isAiResponding}>
                Send
              </button>
            </form>
          </div>
        );
      case 'inventory':
        return (
          <div className="inventory-container">
            <h4>Inventory</h4>
            <div className="inventory-money">
              <span className="money-icon">💰</span> {character?.money || 0} pesos
            </div>
            {inventoryItems.length > 0 ? (
              <div className="inventory-items">
                {inventoryItems.map(item => (
                  <div 
                    key={item.id} 
                    className="inventory-item"
                    onClick={() => handleItemClick(item)}
                  >
                    <div className="item-header">
                      <h5>{item.name}</h5>
                      <span className="item-type">{item.type}</span>
                    </div>
                    <p className="item-description">{item.effect_description}</p>
                    {item.armor_class > 0 && <div className="item-stat">Armor: +{item.armor_class}</div>}
                    {item.str > 0 && <div className="item-stat">STR: +{item.str}</div>}
                    {item.dex > 0 && <div className="item-stat">DEX: +{item.dex}</div>}
                    {item.constitution > 0 && <div className="item-stat">CON: +{item.constitution}</div>}
                    {item.intelligence > 0 && <div className="item-stat">INT: +{item.intelligence}</div>}
                    {item.wisdom > 0 && <div className="item-stat">WIS: +{item.wisdom}</div>}
                    {item.charisma > 0 && <div className="item-stat">CHA: +{item.charisma}</div>}
                    {item.equippable && (
                      <button 
                        className="equip-button-list"
                        onClick={(e) => handleEquipItemFromList(e, item)}
                      >
                        {item.is_equipped ? "Unequip" : "Equip"}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p>You don't have any items yet.</p>
            )}
          </div>
        );
      case 'equipment':
        return (
          <div className="equipment-container">
            <h4>Equipment</h4>
            {equippedItems.length > 0 ? (
              <div className="inventory-items">
                {equippedItems.map(item => (
                  <div 
                    key={item.id} 
                    className="inventory-item equipped-item"
                    onClick={() => handleItemClick(item)}
                  >
                    <div className="item-header">
                      <h5>{item.name}</h5>
                      <span className="item-type">{item.type}</span>
                    </div>
                    <p className="item-description">{item.effect_description}</p>
                    {item.armor_class > 0 && <div className="item-stat">Armor: +{item.armor_class}</div>}
                    {item.str > 0 && <div className="item-stat">STR: +{item.str}</div>}
                    {item.dex > 0 && <div className="item-stat">DEX: +{item.dex}</div>}
                    {item.constitution > 0 && <div className="item-stat">CON: +{item.constitution}</div>}
                    {item.intelligence > 0 && <div className="item-stat">INT: +{item.intelligence}</div>}
                    {item.wisdom > 0 && <div className="item-stat">WIS: +{item.wisdom}</div>}
                    {item.charisma > 0 && <div className="item-stat">CHA: +{item.charisma}</div>}
                    <button 
                      className="equip-button-list"
                      onClick={(e) => handleEquipItemFromList(e, item)}
                    >
                      Unequip
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p>You don't have any equipped items.</p>
            )}
          </div>
        );
      case 'quests':
        return (
          <div className="quests-container">
            <h4>Quest Log</h4>
            {quests.length > 0 ? (
              <div className="quest-list">
                {quests.map(quest => (
                  <div key={quest.id} className={`quest-item ${quest.completed ? 'completed' : ''}`}>
                    <div className="quest-header">
                      <h5>{quest.title}</h5>
                      <span className={`quest-status ${quest.completed ? 'completed' : ''}`}>
                        {quest.completed ? '✓ Complete' : '⋯ In Progress'}
                      </span>
                    </div>
                    <p className="quest-description">{quest.description}</p>
                    <div className="quest-rewards">
                      <span>Rewards: </span>
                      {quest.reward_money > 0 && <span className="reward-money">{quest.reward_money} pesos</span>}
                      {quest.reward_item && <span className="reward-item">{quest.reward_item.name}</span>}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p>No quests available.</p>
            )}
          </div>
        );
      case 'logs':
        return (
          <div className="logs-container">
            <h4>Adventure Log</h4>
            <p>Your adventure notes will appear here.</p>
          </div>
        );
      default:
        return null;
    }
  };

  // Fallback for loading state
  if (loading) {
    return (
      <div className="main-container">
        <header className="game-header">
          <h1>Emerald Altar</h1>
        </header>
        <div className="loading">Loading character data...</div>
      </div>
    );
  }
  
  // Fallback for error state
  if (error) {
    return (
      <div className="main-container">
        <header className="game-header">
          <h1>Emerald Altar</h1>
          <button onClick={handleLogout}>Logout</button>
        </header>
        <div className="error-container">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Try Again</button>
        </div>
      </div>
    );
  }

  return (
    <div className="main-container">
      <header className="game-header">
        <h1>Emerald Altar</h1>
        <nav>
          <button onClick={handleLogout} className="logout-button">Logout</button>
        </nav>
      </header>
      
      <div className="game-content">
        {character ? (
          <div className="character-info">
            <div className="character-avatar">
              <img src={character.avatar_url} alt={character.name} />
            </div>
            <h2>{character.name}</h2>
            <div className="character-level-container">
              <span className="character-level">Level {Math.floor(character.exp / 100) + 1}</span>
            </div>
            <p className="character-class">Class: {character.class_?.name}</p>
            <p className="character-race">Race: {character.race}</p>
            {character.background && <p className="character-background">Background: {character.background}</p>}
            {character.description && <p className="character-description">"{character.description}"</p>}
            
            <div className="character-stats">
              <div className="stat">
                <span>HP</span>
                <div className="progress-bar">
                  <div 
                    className="progress" 
                    style={{ width: `${(character.hp_status / character.class_?.hp) * 100}%` }}
                  ></div>
                </div>
                <span>{character.hp_status}/{character.class_?.hp}</span>
              </div>
              <div className="stat">
                <span>MP</span>
                <div className="progress-bar">
                  <div 
                    className="progress" 
                    style={{ width: `${(character.mp_status / character.class_?.mp) * 100}%` }}
                  ></div>
                </div>
                <span>{character.mp_status}/{character.class_?.mp}</span>
              </div>
              <div className="stat">
                <span>EXP</span>
                <div className="progress-bar">
                  <div 
                    className="progress" 
                    style={{ width: `${(character.exp % 100) / 100 * 100}%` }}
                  ></div>
                </div>
                <span>{character.exp % 100}/100</span>
              </div>
            </div>

            <div className="character-attributes">
              <h3>Attributes</h3>
              <div className="attributes-grid">
                <div className="attribute">
                  <span>Armor Class</span>
                  <span>{character.class_?.armor_class || 0}</span>
                </div>
                <div className="attribute">
                  <span>Strength</span>
                  <span>{character.class_?.strength || character.class_?.str || 0}</span>
                </div>
                <div className="attribute">
                  <span>Dexterity</span>
                  <span>{character.class_?.dexterity || character.class_?.dex || 0}</span>
                </div>
                <div className="attribute">
                  <span>Constitution</span>
                  <span>{character.class_?.constitution || 0}</span>
                </div>
                <div className="attribute">
                  <span>Intelligence</span>
                  <span>{character.class_?.intelligence || 0}</span>
                </div>
                <div className="attribute">
                  <span>Wisdom</span>
                  <span>{character.class_?.wisdom || 0}</span>
                </div>
                <div className="attribute">
                  <span>Charisma</span>
                  <span>{character.class_?.charisma || 0}</span>
                </div>
                <div className="attribute">
                  <span>Initiative</span>
                  <span>{character.class_?.initiative || 0}</span>
                </div>
                <div className="attribute">
                  <span>Speed</span>
                  <span>{character.class_?.speed || 0}</span>
                </div>
              </div>
            </div>

            <div className="character-moves">
              <h3>Moves</h3>
              <div className="moves-list">
                {character.class_?.moves?.map((move, index) => (
                  <div key={index} className="move-card">
                    <h4>{move.name}</h4>
                    <p>{move.description}</p>
                    <div className="move-details">
                      <span>Damage: {move.damage}</span>
                      <span>MP Cost: {move.mana_cost}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="character-creation">
            <h2>Create a Character</h2>
            <p>You don't have a character yet. Create one to begin your adventure.</p>
            <button className="action-button">Create Character</button>
          </div>
        )}
        
        <div className="game-area">
          <h3>Game World</h3>
          
          <div className="tab-buttons">
            <button 
              className={`tab-button ${activeTab === 'game' ? 'active' : ''}`}
              onClick={() => setActiveTab('game')}
            >
              Game
            </button>
            <button 
              className={`tab-button ${activeTab === 'inventory' ? 'active' : ''}`}
              onClick={() => setActiveTab('inventory')}
            >
              Inventory
            </button>
            <button 
              className={`tab-button ${activeTab === 'equipment' ? 'active' : ''}`}
              onClick={() => setActiveTab('equipment')}
            >
              Equipment
            </button>
            <button 
              className={`tab-button ${activeTab === 'quests' ? 'active' : ''}`}
              onClick={() => setActiveTab('quests')}
            >
              Quests
            </button>
            <button 
              className={`tab-button ${activeTab === 'logs' ? 'active' : ''}`}
              onClick={() => setActiveTab('logs')}
            >
              Logs
            </button>
          </div>
          
          <div className="tab-content">
            {renderTabContent()}
          </div>
        </div>
        
        <div className="dice-panel">
          <h3>Dice Roller</h3>
          <div className="dice-result">
            {diceResult ? (
              <div className="dice-value">
                <span className="dice-number">{diceResult.result}</span>
                <span className="dice-type">d{diceResult.sides}</span>
              </div>
            ) : (
              <div className="dice-placeholder">Roll a die</div>
            )}
          </div>
          <div className="dice-tooltip">
            <small>Dice rolls in Game tab are automatically sent to chat</small>
          </div>
          <div className="dice-buttons">
            <button 
              className={`dice-button d20 ${rollingDie === 20 ? 'rolling' : ''}`} 
              onClick={() => rollDice(20)} 
              disabled={rollingDie !== null}
            >
              d20
            </button>
            <button 
              className={`dice-button d12 ${rollingDie === 12 ? 'rolling' : ''}`} 
              onClick={() => rollDice(12)} 
              disabled={rollingDie !== null}
            >
              d12
            </button>
            <button 
              className={`dice-button d8 ${rollingDie === 8 ? 'rolling' : ''}`} 
              onClick={() => rollDice(8)} 
              disabled={rollingDie !== null}
            >
              d8
            </button>
            <button 
              className={`dice-button d6 ${rollingDie === 6 ? 'rolling' : ''}`} 
              onClick={() => rollDice(6)} 
              disabled={rollingDie !== null}
            >
              d6
            </button>
            <button 
              className={`dice-button d4 ${rollingDie === 4 ? 'rolling' : ''}`} 
              onClick={() => rollDice(4)} 
              disabled={rollingDie !== null}
            >
              d4
            </button>
          </div>
        </div>
      </div>
      
      {/* Item Detail Modal */}
      {showItemModal && selectedItem && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{selectedItem.name}</h2>
              <span className="item-type-modal">{selectedItem.type}</span>
              <button className="close-modal" onClick={handleCloseModal}>×</button>
            </div>
            
            <div className="modal-body">
              <div className="item-image-container">
                {selectedItem.image_url ? (
                  <img 
                    src={selectedItem.image_url} 
                    alt={selectedItem.name} 
                    className="item-image"
                  />
                ) : (
                  <div className="item-image-placeholder">
                    <span>No image available</span>
                  </div>
                )}
              </div>
              
              <div className="item-details">
                <div className="item-description-container">
                  <h4>Description</h4>
                  <p>{selectedItem.effect_description || "No description available."}</p>
                </div>
                
                {selectedItem.lore_description && (
                  <div className="item-lore-container">
                    <h4>Lore</h4>
                    <p>{selectedItem.lore_description}</p>
                  </div>
                )}
                
                <div className="item-stats-container">
                  <h4>Statistics</h4>
                  <div className="item-stats-grid">
                    {selectedItem.armor_class > 0 && (
                      <div className="item-stat-detail">
                        <span>Armor Class</span>
                        <span>+{selectedItem.armor_class}</span>
                      </div>
                    )}
                    {selectedItem.str > 0 && (
                      <div className="item-stat-detail">
                        <span>Strength</span>
                        <span>+{selectedItem.str}</span>
                      </div>
                    )}
                    {selectedItem.dex > 0 && (
                      <div className="item-stat-detail">
                        <span>Dexterity</span>
                        <span>+{selectedItem.dex}</span>
                      </div>
                    )}
                    {selectedItem.constitution > 0 && (
                      <div className="item-stat-detail">
                        <span>Constitution</span>
                        <span>+{selectedItem.constitution}</span>
                      </div>
                    )}
                    {selectedItem.intelligence > 0 && (
                      <div className="item-stat-detail">
                        <span>Intelligence</span>
                        <span>+{selectedItem.intelligence}</span>
                      </div>
                    )}
                    {selectedItem.wisdom > 0 && (
                      <div className="item-stat-detail">
                        <span>Wisdom</span>
                        <span>+{selectedItem.wisdom}</span>
                      </div>
                    )}
                    {selectedItem.charisma > 0 && (
                      <div className="item-stat-detail">
                        <span>Charisma</span>
                        <span>+{selectedItem.charisma}</span>
                      </div>
                    )}
                    {selectedItem.initiative > 0 && (
                      <div className="item-stat-detail">
                        <span>Initiative</span>
                        <span>+{selectedItem.initiative}</span>
                      </div>
                    )}
                    {selectedItem.speed > 0 && (
                      <div className="item-stat-detail">
                        <span>Speed</span>
                        <span>+{selectedItem.speed}</span>
                      </div>
                    )}
                    {selectedItem.weight > 0 && (
                      <div className="item-stat-detail">
                        <span>Weight</span>
                        <span>{selectedItem.weight} lbs</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
            
            <div className="modal-footer">
              <button 
                className="equip-button"
                onClick={handleEquipItem}
              >
                {selectedItem.is_equipped ? "Unequip" : "Equip"}
              </button>
              <button className="close-button" onClick={handleCloseModal}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Main;

