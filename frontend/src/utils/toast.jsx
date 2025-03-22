import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

// Function to trigger toast messages
export const showToast = (message, type = "error", autoClose = 5000) => {
  toast[type](message, { autoClose });
};

// Export a reusable ToastContainer component
export const ToastWrapper = ({ position = "top-right", autoClose = 5000 }) => {
  return <ToastContainer position={position} autoClose={autoClose} />;
};
