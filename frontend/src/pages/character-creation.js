import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import "../styles/character-creation.css"

function CharacterCreation() {
  const [classes, setClasses] = useState([]);
  const [selectedClass, setSelectedClass] = useState(null);
  const [showClassModal, setShowClassModal] = useState(false);
  const [showMovesModal, setShowMovesModal] = useState(false);
  const [characterName, setCharacterName] = useState('');
  const [characterDescription, setCharacterDescription] = useState('');
  const [avatarUrl, setAvatarUrl] = useState('/default-avatar.png');
  const [isGeneratingAvatar, setIsGeneratingAvatar] = useState(false);
  const [isGeneratingBio, setIsGeneratingBio] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // Fetch available classes on component mount
  useEffect(() => {
    const fetchClasses = async () => {
      try {
        const response = await fetch('http://127.0.0.1:5000/api/classes');
        if (!response.ok) {
          throw new Error('Failed to fetch classes');
        }
        const data = await response.json();
        setClasses(data);
      } catch (err) {
        console.error('Error fetching classes:', err);
        setError('Failed to load classes. Please try again.');
      }
    };

    fetchClasses();
  }, []);

  // Fetch class moves when a class is selected
  useEffect(() => {
    const fetchClassMoves = async () => {
      if (!selectedClass) return;

      try {
        const response = await fetch(`http://127.0.0.1:5000/api/classes/${selectedClass.id}/moves`);
        if (!response.ok) {
          throw new Error('Failed to fetch class moves');
        }
        const moves = await response.json();
        setSelectedClass(prev => ({ ...prev, moves }));
      } catch (err) {
        console.error('Error fetching class moves:', err);
        setError('Failed to load class moves. Please try again.');
      }
    };

    fetchClassMoves();
  }, [selectedClass?.id]);

  const handleClassSelect = (classData) => {
    setSelectedClass(classData);
    setShowClassModal(true);
  };

  const handleGenerateAvatar = async () => {
    if (!characterName || !selectedClass) {
      setError('Please enter a character name and select a class first');
      return;
    }

    setIsGeneratingAvatar(true);
    setError('');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://127.0.0.1:5000/api/generate-avatar', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          character_name: characterName,
          character_class: selectedClass.name,
          character_description: characterDescription
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || 'Failed to generate avatar');
      }

      const data = await response.json();
      setAvatarUrl(data.image_url);
    } catch (err) {
      console.error('Error generating avatar:', err);
      setError(err.message || 'Failed to generate avatar. Please try again.');
    } finally {
      setIsGeneratingAvatar(false);
    }
  };

  const handleGenerateBio = async () => {
    if (!characterName || !selectedClass) {
      setError('Please enter a character name and select a class first');
      return;
    }

    setIsGeneratingBio(true);
    setError('');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://127.0.0.1:5000/api/generate-bio', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          character_name: characterName,
          character_class: selectedClass.name
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || 'Failed to generate bio');
      }

      const data = await response.json();
      setCharacterDescription(data.bio);
    } catch (err) {
      console.error('Error generating bio:', err);
      setError(err.message || 'Failed to generate bio. Please try again.');
    } finally {
      setIsGeneratingBio(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (!selectedClass) {
      setError('Please select a class');
      setLoading(false);
      return;
    }

    if (!characterName.trim()) {
      setError('Please enter a character name');
      setLoading(false);
      return;
    }

    try {
      const user = JSON.parse(localStorage.getItem('user'));
      const token = localStorage.getItem('token');

      const response = await fetch('http://127.0.0.1:5000/api/characters', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: characterName,
          race: 'Human', // Default race for now
          exp: 0,
          avatar_url: avatarUrl, // Use the generated avatar URL
          class_id: selectedClass.id,
          description: characterDescription,
          user_id: user.id,
          hp_status: selectedClass.hp, // Set initial HP to class's base HP
          mp_status: selectedClass.mp  // Set initial MP to class's base MP
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || 'Failed to create character');
      }

      const characterData = await response.json();
      
      // Update user's character_id
      const userResponse = await fetch(`http://127.0.0.1:5000/api/users/${user.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          character_id: characterData.id
        }),
      });

      if (!userResponse.ok) {
        throw new Error('Failed to update user with character');
      }

      // Navigate to main page
      navigate(`/main/${user.id}`);
    } catch (err) {
      console.error('Error creating character:', err);
      setError(err.message || 'Failed to create character. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="character-creation-container">
      <div className="creation-content">
        {/* Left side - Character Info */}
        <div className="character-info">
          <h2>Character Details</h2>
          <div className="avatar-placeholder">
            <img src={avatarUrl} alt="Character Avatar" />
            <div className="avatar-controls">
              <button 
                className="generate-button"
                onClick={handleGenerateAvatar}
                disabled={isGeneratingAvatar || !characterName || !selectedClass}
              >
                {isGeneratingAvatar ? 'Generating...' : 'Generate Avatar'}
              </button>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}

          <form onSubmit={handleSubmit} className="character-form">
            <div className="form-group">
              <label htmlFor="characterName">Character Name</label>
              <input
                type="text"
                id="characterName"
                value={characterName}
                onChange={(e) => setCharacterName(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="characterDescription">Character Description</label>
              <div className="description-container">
                <textarea
                  id="characterDescription"
                  value={characterDescription}
                  onChange={(e) => setCharacterDescription(e.target.value)}
                  rows="4"
                  disabled={loading || isGeneratingBio}
                />
                <button 
                  type="button"
                  className="generate-button"
                  onClick={handleGenerateBio}
                  disabled={isGeneratingBio || !characterName || !selectedClass}
                >
                  {isGeneratingBio ? 'Generating...' : 'Generate Bio'}
                </button>
              </div>
            </div>

            <button type="submit" className="create-button" disabled={loading}>
              {loading ? 'Creating...' : 'Create Character'}
            </button>
          </form>
        </div>

        {/* Right side - Class Selection */}
        <div className="class-selection">
          <h2>Choose Your Class</h2>
          <div className="class-grid">
            {classes.map(classData => (
              <div
                key={classData.id}
                className={`class-card ${selectedClass?.id === classData.id ? 'selected' : ''}`}
                onClick={() => handleClassSelect(classData)}
              >
                <h3>{classData.name}</h3>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Class Details Modal */}
      {showClassModal && selectedClass && (
        <div className="modal-overlay" onClick={() => setShowClassModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>{selectedClass.name}</h2>
            <div className="class-full-description">
              <h3>Description</h3>
              <p>{selectedClass.description}</p>
            </div>
            <div className="class-stats">
              <div className="stat-group">
                <h3>Base Stats</h3>
                <p>HP: {selectedClass.hp}</p>
                <p>MP: {selectedClass.mp}</p>
                <p>Armor Class: {selectedClass.armor_class}</p>
              </div>
              <div className="stat-group">
                <h3>Attributes</h3>
                <p>Strength: {selectedClass.str}</p>
                <p>Dexterity: {selectedClass.dex}</p>
                <p>Speed: {selectedClass.speed}</p>
                <p>Wisdom: {selectedClass.wisdom}</p>
                <p>Intelligence: {selectedClass.intelligence}</p>
                <p>Constitution: {selectedClass.constitution}</p>
                <p>Charisma: {selectedClass.charisma}</p>
              </div>
            </div>
            <div className="modal-actions">
              <button onClick={() => setShowMovesModal(true)}>View Moves</button>
              <button onClick={() => setShowClassModal(false)}>Close</button>
            </div>
          </div>
        </div>
      )}

      {/* Moves Modal */}
      {showMovesModal && selectedClass && (
        <div className="modal-overlay" onClick={() => setShowMovesModal(false)}>
          <div className="modal-content moves-modal" onClick={e => e.stopPropagation()}>
            <h2>{selectedClass.name} Moves</h2>
            <div className="moves-list">
              {selectedClass.moves?.map(move => (
                <div key={move.id} className="move-card">
                  <h4>{move.name}</h4>
                  <p>{move.description}</p>
                  <div className="move-stats">
                    <span>Damage: {move.damage}</span>
                    <span>Mana Cost: {move.mana_cost}</span>
                    {move.status_effect && <span>Status: {move.status_effect}</span>}
                  </div>
                </div>
              ))}
            </div>
            <button onClick={() => setShowMovesModal(false)}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default CharacterCreation;