import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { apiRequest } from "../functions";
import { showToast } from "../utils/toast";

const GoogleCallback = ({ isAuthenticated, setIsAuthenticated }) => {
  const navigate = useNavigate();

  // useEffect(() => {
  //   document.title = 'Logging with Google...';
  //   if (isAuthenticated) {
  //     navigate("/");
  //   }
  // }, []);

  useEffect(() => {
    const handleGoogleLogin = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get("code");
      const state = urlParams.get("state" || "web");

      if (!code) {
        showToast("Google login failed: No authorization code", "error");
        navigate("/login");
        return;
      }

      try {
        const response = await apiRequest({ API: `/google-auth/callback?code=${encodeURIComponent(code)}&state=${state}`, METHOD: "GET", ACCESS_TOKEN_REQUIRED: false });

        if (response.success && response.access_token) {
          // if is_app_redirect_url 
          if (response.auth_type === "app") {
            const deepLink = `whatbmphotos://google-auth/callback?access_token=${encodeURIComponent(response.access_token)}&refresh_token=${encodeURIComponent(response.refresh_token)}`;
            window.location.href = deepLink;
            setTimeout(() => {
              const lastPath = "/";
              navigate(lastPath, { replace: true });
            }, 2000);
          // else mean web version 
          }else{
            localStorage.setItem("access_token", response.access_token);
            showToast("Login successful!", "success");
            setIsAuthenticated(true);
            const lastPath = localStorage.getItem("lastPath") || "/";
            localStorage.removeItem("lastPath");
            navigate(lastPath, { replace: true });
          }
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
