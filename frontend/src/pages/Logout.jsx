import React, { useState, useEffect } from "react";
import "../styles/Logout.css";
import { apiRequest } from "../functions";
import { useNavigate } from "react-router-dom";

const LogoutModal = ({ isAuthenticated, setIsAuthenticated }) => {
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        document.title = "Logout";
        if (!isAuthenticated) {
            navigate("/");
        }
    }, []);

    const handleLogout = async (allDevices) => {
        setLoading(true);
    
        try {
            const response = await apiRequest({API:'/logout', DATA:{ allDevices }});
    
            if (response.success) {
                navigate("/");
            } 
        } catch (error) {
            alert(error.message || "An error occurred");
        } finally {
            setLoading(false);
            localStorage.removeItem('access_token');
            setIsAuthenticated(false);
        }
    };
    

    return (
        <div className="modal-overlay">
            <div className="modal">
                <p className="modal-text">Are you sure you want to logout?</p>
                <div className="modal-buttons">
                    <button 
                        className="logout-all" 
                        onClick={() => handleLogout(true)}
                        disabled={loading}
                    >
                        {loading ? "Logging out..." : "Logout from All Devices"}
                    </button>
                    <button 
                        className="logout" 
                        onClick={() => handleLogout(false)}
                        disabled={loading}
                    >
                        {loading ? "Logging out..." : "Logout"}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default LogoutModal;
