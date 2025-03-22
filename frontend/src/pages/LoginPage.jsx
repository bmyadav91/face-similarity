import React, { useState, useEffect } from "react";
import "../styles/Login.css";
import googleIcon from "../assets/img/google.svg";
import { apiRequest } from "../functions";
import { showToast } from "../utils/toast";
import { useNavigate } from "react-router-dom";

const LoginPage = ({ isAuthenticated, setIsAuthenticated }) => {
  const navigate = useNavigate();

  useEffect(() => {
    document.title = 'Login';
    if (isAuthenticated) {
      const lastPath = localStorage.getItem("lastPath") || "/";
      localStorage.removeItem("lastPath");
      navigate(lastPath, { replace: true });
    }
  }, [])

  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [name, setName] = useState("");
  const [showOtpField, setShowOtpField] = useState(false);
  const [showNameField, setShowNameField] = useState(false);
  const [isLoading, setIsLoading] = useState(false);



  const handleSubmit = async () => {
    if (!email || email.length < 5 || email.length > 50) {
      showToast("Please enter a valid email", "error");
      return;
    }

    if (showOtpField && (otp.length < 4 || otp.length > 10)) {
      showToast("OTP should be 4 digits", "error");
      return;
    }

    setIsLoading(true);
    let shouldEnableButton = true;

    try {
      const endpoint = showOtpField ? "/verify_otp" : "/send_otp";
      const payload = showOtpField ? { email, otp } : { email };

      const response = await apiRequest({ API: endpoint, DATA: payload, ACCESS_TOKEN_REQUIRED: false });

      if (response.success) {
        if (showOtpField) {
          if (response.access_token) {
            localStorage.setItem("access_token", response.access_token);
            setIsAuthenticated(true);
          }

          if (response.need_name_update) {
            setShowNameField(true);
          } else {
            shouldEnableButton = false;
            const lastPath = localStorage.getItem("lastPath") || "/";
            localStorage.removeItem("lastPath");
            navigate(lastPath, { replace: true });
            showToast("Login successful", "success");
          }
        } else {
          setShowOtpField(true);
        }
      } else {
        showToast(response.error || "Something went wrong", "error");
      }
    } catch (error) {
      showToast(error.message || "An error occurred", "error");
    } finally {
      if (shouldEnableButton) setIsLoading(false);
    }
  };

  const handleUpdateName = async () => {
    if (!name || name.length < 1 || name.length > 50) {
      showToast("Please enter a valid name", "error");
      return;
    }

    setIsLoading(true);

    try {
      const response = await apiRequest({ API: "/change-name", DATA: { name: name } });

      if (response.success) {
        showToast("Name updated successfully!", "success");
        navigate("/");
      } else {
        showToast(response.error || "Failed to update name", "error");
      }
    } catch (error) {
      showToast(error.message || "An error occurred", "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setIsLoading(true);
    let shouldEnableButton = true;

    const currentDomain = window.location.origin;

    try {
      const response = await apiRequest({ API: `/google-auth?domain=${encodeURIComponent(currentDomain)}`, METHOD: "GET", ACCESS_TOKEN_REQUIRED: false });

      if (response.success && response.auth_url) {
        window.location.href = response.auth_url;
        shouldEnableButton = false;
      } else {
        showToast(response.message || "Failed to get Google auth URL", "error");
      }
    } catch (error) {
      showToast(error.message || "An error occurred", "error");
    } finally {
      if (shouldEnableButton) setIsLoading(false);
    }
  };

  return (
    <section className="login_container forms">
      <div className="form login">
        <div className="form-content">
          <h1 className="header">Login</h1>
          <form onSubmit={(e) => e.preventDefault()}>
            {!showNameField && (
              <>
                <div className="field input-field">
                  <input
                    type="email"
                    name="email"
                    placeholder="Email"
                    className="input"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>

                {showOtpField && (
                  <div className="field input-field">
                    <input
                      type="number"
                      name="otp"
                      placeholder="OTP"
                      value={otp}
                      onChange={(e) => setOtp(e.target.value)}
                    />
                  </div>
                )}
              </>
            )}

            {showNameField && (
              <div className="field input-field">
                <input
                  type="text"
                  name="name"
                  placeholder="Enter your name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
            )}

            <div className="field button-field">
              {!showNameField ? (
                <button onClick={handleSubmit} disabled={isLoading}>
                  {isLoading ? "Processing..." : showOtpField ? "Verify OTP" : "Send OTP"}
                </button>
              ) : (
                <button onClick={handleUpdateName} disabled={isLoading}>
                  {isLoading ? "Updating Name..." : "Update Name"}
                </button>
              )}
            </div>
          </form>
        </div>

        <div className="line"></div>

        <div className="other-login-options">
          <button onClick={handleGoogleLogin} className="field" disabled={isLoading}>
            <div>
              <img src={googleIcon} alt="Login with Google" />
              {isLoading ? "Logging in..." : "Login with Google"}
            </div>
          </button>
        </div>
      </div>
    </section>
  );
};

export default LoginPage;
