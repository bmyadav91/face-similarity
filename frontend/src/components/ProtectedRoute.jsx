import { Navigate, useLocation } from "react-router-dom";

const ProtectedRoute = ({ isAuthenticated, children }) => {
  const location = useLocation();

  if (!isAuthenticated) {
    localStorage.setItem("lastPath", location.pathname);
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default ProtectedRoute;
