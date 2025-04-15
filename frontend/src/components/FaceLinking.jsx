import React from "react";
import { motion } from "framer-motion";
import { showToast } from "../utils/toast";
import "../styles/FaceLinking.css";
import { apiRequest } from "../functions";

const FaceLinking = ({ photo_id, onClose }) => {
    const [error, setError] = React.useState(null);
    const [faces, setFaces] = React.useState([]);
    const [hasMoreFaces, setHasMoreFaces] = React.useState(false);
    const [page, setPage] = React.useState(1);
    const [isLoading, setIsLoading] = React.useState(false);

    // Fetch faces from API
    const FetchFace = async (photo_id, page = 1) => {
        try {
            if (!photo_id) return;
            setIsLoading(true);
            const response = await apiRequest({ API: `/get_faces`, DATA: { photo_id, page } });
            if (response.success) {
                setHasMoreFaces(response.has_next || false);
                setPage(response.page || page);
                setFaces((prev) => [...prev, ...response.faces]); 
            } else {
                showToast(response.message || "Failed to fetch faces", "error");
            }
        } catch (error) {
            console.error("Error fetching faces:", error);
            setError(error.message);
            showToast(error.message || "Failed to fetch faces", "error");
            return;
        } finally {
            setIsLoading(false);
        }
    };

    // Link/unlink photo to face
    const LinkUnlinkPhotoWithFace = async (photo_id, face_id, checked) => {
        try {
            setIsLoading(true);
            const response = await apiRequest({ API: `/link_unlink_photo_with_face`, DATA: { photo_id, face_id, checked } });
            if (response.success) {
                showToast(response.message || "Face updated successfully!", "success");
                onClose();
            } else {
                showToast(response.message || "Failed to link face", "error");
            }
        } catch (error) {
            console.error("Error linking face:", error);
            setError(error.message);
            showToast(error.message || "Failed to link face", "error");
            return;
        } finally {
            setIsLoading(false);
        }
    };

    React.useEffect(() => {
        FetchFace(photo_id, page);
    }, []);

    if (error) return null;

    return (
        <div className="add_to_face_parent" onClick={onClose}>
            <motion.div
                className="modal"
                initial={{ y: "100%" }}
                animate={{ y: "0%" }}
                exit={{ y: "100%" }}
                onClick={(e) => e.stopPropagation()}
            >
                <div className="modal-header">
                    Add to
                    <span className="close-btn" onClick={onClose}>×</span>
                </div>
                <div className="modal-content">
                    {faces.length > 0 ? (
                        faces.map((face, index) => (
                            <div className="album" key={index}>
                                <input
                                    type="checkbox"
                                    id={`album1-${face.id}`}
                                    disabled={isLoading}
                                    checked={face.linked}
                                    onChange={(e) => LinkUnlinkPhotoWithFace(photo_id, face.id, e.target.checked)}
                                />
                                <img src={face.face_url} alt={face.name || "Untitled"} />
                                <div className="album-details">
                                    <span className="album-title">{face.name || "Untitled"}</span>
                                    <span className="contained_items">{face.face_count} items</span>
                                </div>
                            </div>
                        ))
                    ) : (
                        <p>{isLoading ? "Loading..." : "No anymore faces"}</p>
                    )}
                    {hasMoreFaces && <button className="btn show_more_btn" onClick={() => FetchFace(photo_id, page + 1)} disabled={isLoading}>{isLoading ? "Working..." : "Show More"}</button>}
                </div>
            </motion.div>
        </div>
    );
};

export default FaceLinking;
