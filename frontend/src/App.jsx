import React, { useEffect, useState, Suspense, lazy } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Header from "./components/Header";
import { isAuthenticatedFun } from "./functions";
import Loader from "./components/Loader";
import { ToastWrapper } from "./utils/toast";
import ProtectedRoute from "./components/ProtectedRoute"; 

const HomePage = lazy(() => import("./pages/HomePage"));
const Logout = lazy(() => import("./pages/Logout"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const GoogleCallback = lazy(() => import("./pages/GoogleCallback"));
const UploadFile = lazy(() => import("./pages/UploadFile"));
const FacePage = lazy(() => import("./pages/Face"));

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const authStatus = await isAuthenticatedFun();
      setIsAuthenticated(authStatus);
      setLoading(false);
    };

    checkAuth();
  }, []);

  if (loading) {
    return <Loader />;
  }

  return (
    <Router>
      <ToastWrapper />
      <Header isAuthenticated={isAuthenticated} />
      <Suspense fallback={<Loader />}>
        <Routes>
          <Route path="/" element={<HomePage isAuthenticated={isAuthenticated} />} />

          {/* Protected Routes */}
          <Route
            path="/face/:id"
            element={
              <ProtectedRoute isAuthenticated={isAuthenticated}>
                <FacePage isAuthenticated={isAuthenticated} />
              </ProtectedRoute>
            }
          />

          <Route
            path="/upload"
            element={
              <ProtectedRoute isAuthenticated={isAuthenticated}>
                <UploadFile isAuthenticated={isAuthenticated} />
              </ProtectedRoute>
            }
          />

          {/* Public Routes */}
          <Route path="/login" element={<LoginPage isAuthenticated={isAuthenticated} setIsAuthenticated={setIsAuthenticated} />} />
          <Route path="/google-auth/callback" element={<GoogleCallback isAuthenticated={isAuthenticated} setIsAuthenticated={setIsAuthenticated} />} />
          <Route path="/logout" element={<Logout isAuthenticated={isAuthenticated} setIsAuthenticated={setIsAuthenticated} />} />
        </Routes>
      </Suspense>
    </Router>
  );
}

export default App;
