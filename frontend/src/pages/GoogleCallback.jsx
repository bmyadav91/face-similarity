import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { apiRequest } from "../functions";
import { showToast } from "../utils/toast";

const GoogleCallback = ({ isAuthenticated, setIsAuthenticated }) => {
  const navigate = useNavigate();

  useEffect(() => {
    document.title = 'Logging with Google...';
    if (isAuthenticated) {
      navigate("/");
    }
  }, []);

  useEffect(() => {
    const handleGoogleLogin = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get("code");

      if (!code) {
        showToast("Google login failed: No authorization code", "error");
        navigate("/login");
        return;
      }

      try {
        const currentDomain = window.location.origin;
        const response = await apiRequest({ API: `/google-auth/callback?code=${encodeURIComponent(code)}&domain=${encodeURIComponent(currentDomain)}`, METHOD: "GET", ACCESS_TOKEN_REQUIRED: false });

        if (response.success && response.access_token) {
          localStorage.setItem("access_token", response.access_token);
          showToast("Login successful!", "success");
          setIsAuthenticated(true);
          const lastPath = localStorage.getItem("lastPath") || "/";
          localStorage.removeItem("lastPath");
          navigate(lastPath, { replace: true });
        } else {
          showToast(response.message || "Google login failed", "error");
          navigate("/login");
        }
      } catch (error) {
        showToast(error.message || "An error occurred", "error");
        navigate("/login");
      }
    };

    handleGoogleLogin();
  }, [navigate]);

  return <p style={{ textAlign: "center", padding: "20px" }}>Processing login...</p>;
};

export default GoogleCallback;
