import { Navigate, useParams } from 'react-router-dom';

// Check if user is logged in
const isAuthenticated = () => {
  const token = localStorage.getItem('token');
  const user = localStorage.getItem('user');
  return token && user;
};

// Get current user ID
const getCurrentUserId = () => {
  const user = localStorage.getItem('user');
  if (user) {
    return JSON.parse(user).id;
  }
  return null;
};

const ProtectedRoute = ({ children }) => {
  const { userId } = useParams();
  
  if (!isAuthenticated()) {
    // Not logged in, redirect to login
    return <Navigate to="/login" replace />;
  }
  
  const currentUserId = getCurrentUserId();
  
  // Check if the user is trying to access their own page
  if (userId && currentUserId !== parseInt(userId)) {
    // Not the correct user, redirect to their own page
    return <Navigate to={`/main/${currentUserId}`} replace />;
  }
  
  return children;
};

export default ProtectedRoute; 