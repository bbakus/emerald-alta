import './App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Landing from './pages/landing';
import Login from './pages/login';
import Signup from './pages/signup';
import Main from './pages/main';
import ProtectedRoute from './components/ProtectedRoute';
import CharacterCreation from './pages/character-creation';

function App() {
  return (
    <BrowserRouter>
      <div className="App">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          
          {/* Protected main route with user ID */}
          <Route 
            path="/main/:userId" 
            element={
              <ProtectedRoute>
                <Main />
              </ProtectedRoute>
            } 
          />

          <Route 
            path="/character-creation/:userId" 
            element={
              <ProtectedRoute>
                <CharacterCreation />
              </ProtectedRoute>
            } 
          />
          
          {/* Redirect /main to /main/userId if logged in */}
          <Route 
            path="/main" 
            element={
              localStorage.getItem('user') 
                ? <Navigate to={`/main/${JSON.parse(localStorage.getItem('user')).id}`} replace /> 
                : <Navigate to="/login" replace />
            } 
          />
          
          {/* Catch all route */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
