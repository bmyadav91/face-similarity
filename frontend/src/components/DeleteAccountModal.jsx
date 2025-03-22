import React from "react";
import "../styles/DeleteAccountModal.css";
import { showToast } from "../utils/toast";
import { apiRequest } from '../functions';

const DeleteModal = ({ onClose }) => {
  const [isDeleting, setIsDeleting] = React.useState(false);

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      const response = await apiRequest({ API: `/delete_account`, METHOD: 'POST' });
      if (response.success) {
        showToast(response.message || "Account deleted successfully!", "success");
        onClose();
        localStorage.removeItem('access_token');
        setTimeout(() => {
          window.location.href = '/login';
        }, 2000);
      }
    } catch (error) {
      showToast(error.message || "Failed to delete account", "error");
    } finally {
      setIsDeleting(false);
    }
  };

  return ( 
    <div className="delete_modal">
      <div className="modal-content">
        <p>Do you want to permanently delete your account?</p>
        <div className="modal-buttons">
          <button className="btn btn-no" onClick={onClose} disabled={isDeleting}>No</button>
          <button className="btn btn-yes" onClick={handleDelete} disabled={isDeleting}>
            {isDeleting ? "Deleting..." : "Yes"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeleteModal;