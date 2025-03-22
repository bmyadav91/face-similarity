import React, { useState, useEffect, lazy, Suspense, useRef } from "react";
import "../styles/Header.css";
import { Link, useLocation } from "react-router-dom";
import Loader from "../components/Loader";
import BrandLogo from "../assets/img/whatbm_photo_logo.png";

const DeleteModal = lazy(() => import("./DeleteAccountModal"));

const Header = ({ isAuthenticated }) => {
  const [dropdownActive, setDropdownActive] = useState(false);
  const [isDeleteModal, setDeleteModal] = useState(false);
  const dropdownRef = useRef(null);

  const location = useLocation();

  useEffect(() => {
    setDropdownActive(false);
  }, [location]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownActive(false);
      }
    };

    // Add event listener
    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      // Cleanup event listener on unmount
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const toggleDropdown = () => {
    setDropdownActive((prev) => !prev);
  };


  return (
    <header>
      <nav>
        <div className="logo">
          <Link to="/">
          <img src={BrandLogo} alt="Logo" />
          </Link>
          {/* <strong className="logo_txt">Face Album</strong> */}
        </div>
        <div className="menu">
          <Link to="/upload">
            <i className="bi bi-cloud-upload-fill"></i>
          </Link>

          <div className="profile_icon_container" ref={dropdownRef}>
            <i className="bi bi-person-circle" id="profile_icon" onClick={toggleDropdown}></i>
            <div className={`mobile_dropdown ${dropdownActive ? "active" : ""}`}>
              <ul>
                {isAuthenticated ? (
                  <>
                    <li>
                      <Link to="/logout">
                        <i className="bi bi-box-arrow-right"></i> Logout
                      </Link>
                    </li>
                    <li>
                      <a onClick={() => setDeleteModal(true)}>
                        <i className="bi bi-trash"></i> Delete Account
                      </a>
                    </li>
                  </>
                ) : (
                  <li>
                    <Link to="/login">
                      <i className="bi bi-person-fill-check"></i> Login
                    </Link>
                  </li>
                )}
                <li>
                  <a href="https://docs.google.com/document/d/1jfO6mh63R0foJQ27ynKl5EiOnAMW8UjdktuJuAsAgv0/edit?usp=sharing" target="_blank">
                    <i className="bi bi-shield-fill"></i> Privacy Policy
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </nav>

      {/* 🛠 Suspense loads only when isDeleteModal is true */}
      {isDeleteModal && (
        <Suspense fallback={<Loader />}>
          <DeleteModal onClose={() => setDeleteModal(false)} />
        </Suspense>
      )}
    </header>
  );
};

export default Header;
