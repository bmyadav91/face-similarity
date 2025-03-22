import React, { useEffect, useState, lazy, Suspense } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import '../styles/Face.css';
import '../styles/PhotoGallery.css';
import { apiRequest } from '../functions';
import InfiniteScroll from "react-infinite-scroll-component";
import LazyImage from "../components/LazyImageLoader";
import Loader from "../components/Loader";
import { showToast } from "../utils/toast";
const FaceLinking = lazy(() => import("../components/FaceLinking"));

const FaceGallery = ({ isAuthenticated = false }) => {
    const { id } = useParams();
    const navigate = useNavigate();

    // State management
    const [face, setFace] = useState(null);
    const [photos, setPhotos] = useState([]);
    const [photoPage, setPhotoPage] = useState(1);
    const [hasMorePhotos, setHasMorePhotos] = useState(true);
    const [isDeleting, setIsDeleting] = useState(false);
    const [isPaginating, setIsPaginating] = useState(false);
    const [selectedImage, setSelectedImage] = useState(null);
    const [isLinkingModal, setIsLinkingModal] = useState(null);
    const [isFirstTimeLoadingPhoto, setIsFirstTimeLoadingPhoto] = useState(true);

    // Fetch face details and gallery photos
    const fetchFaceDetails = async () => {
        if (!id || isNaN(id)) {
            navigate('/');
            return;
        }

        try {
            // Fetch face details
            const faceResponse = await apiRequest({ API: `/face/${id}`, METHOD: 'GET' });
            if (faceResponse.success) {
                setFace(faceResponse.face);
                document.title = faceResponse.face.name || 'Face Album | Face';
            }

        } catch (error) {
            console.error('Error fetching data:', error);
            showToast('Failed to fetch data. Please try again.', 'error');
        }
    };

    const PhotosByFace = async (page = 1) => {
        setIsPaginating(true);
        try {
            // Fetch gallery photos
            const galleryResponse = await apiRequest({ API: `/photo_by_face?face_id=${id}&page=${page}`, METHOD: 'GET' });
            if (galleryResponse.success) {
                setPhotos(prev => [...prev, ...galleryResponse.photos]);
                setHasMorePhotos(galleryResponse.has_next);
                setPhotoPage(prevPage => prevPage + 1);

                // Update only on the first fetch
                if (isFirstTimeLoadingPhoto) {
                    setIsFirstTimeLoadingPhoto(false);
                }
            }
        } catch (error) {
            console.error('Error fetching data:', error);
            showToast('Failed to fetch data. Please try again.', 'error');
        } finally {
            setIsPaginating(false);
        }
    }

    // update name 
    const handleBlur = async (e) => {
        const newName = e.target.innerText.trim();
        if (newName === face?.name) return;

        try {
            const response = await apiRequest({ API: `/update-face-name`, DATA: { face_id: face.id, name: newName }, METHOD: 'POST' });
            if (response.success) {
                fetchFaceDetails();
                showToast("Name updated successfully!", "success");
            } else {
                showToast(response.message || "Failed to update name", "error");
            }
        } catch (error) {
            showToast(error.message || "Failed to update name", "error");
        }
    };

    // handle delete face 
    const handleDeleteFace = async () => {
        setIsDeleting(true);
        try {
            const response = await apiRequest({ API: `/delete_face`, DATA: { face_id: face.id }, METHOD: 'POST' });
            if (response.success) {
                showToast("Face deleted successfully!", "success");
                navigate('/');
            } else {
                showToast(response.message || "Failed to delete face", "error");
            }
        } catch (error) {
            showToast(error.message || "Failed to delete face", "error");
        } finally {
            setIsDeleting(false);
        }
    };


    // Initial data fetch
    useEffect(() => {
        fetchFaceDetails();
        PhotosByFace(photoPage);
    }, [id, isAuthenticated]);

    // Delete a photo
    const deletePhoto = async (photo_id) => {
        if (isDeleting) {
            showToast("Please wait...", "info");
            return;
        }

        setIsDeleting(true);
        try {
            const response = await apiRequest({ API: `/delete_photo`, DATA: { photo_id }, METHOD: 'POST' });
            if (response.success) {
                setPhotos(prev => prev.filter(photo => photo.id !== photo_id));
                showToast("Photo deleted successfully!", "success");
            }
        } catch (error) {
            showToast(error.message || "Failed to delete photo", "error");
        } finally {
            setIsDeleting(false);
        }
    };

    // Download an image
    const downloadImage = (url, filename) => {
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = filename || "download.jpg";
        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);
    };

    return (
        <main className="container bg-white">
            {/* Face Details */}
            {face && (
                <div className="face_details">
                    <div className="face_img_parent">
                        <img src={face.face_url} alt={face.name || 'Untitled'} className="face_img" />
                    </div>
                    <div className="face_info">
                        <h2
                            className="face_name"
                            contentEditable={true}
                            suppressContentEditableWarning={true}
                            onBlur={handleBlur}
                        >
                            {face.name || 'Untitled'}
                        </h2>
                        <button
                            className="custom_btn"
                            id="delete_face"
                            data-face-id={face.id}
                            title="All photos will be deleted with this face"
                            onClick={handleDeleteFace}
                            disabled={isDeleting}
                        >
                            Delete All ({face.face_count})
                        </button>
                    </div>
                </div>
            )}

            {/* Gallery Section */}
            {photos.length > 0 ? (
                <InfiniteScroll
                    dataLength={photos.length}
                    next={() => PhotosByFace(photoPage)}
                    hasMore={hasMorePhotos}
                    loader={<button style={{ textAlign: 'center' }} className='show_more_btn' onClick={() => PhotosByFace(photoPage)} disabled={isPaginating}>{isPaginating ? 'Loading...' : 'Show More'}</button>}
                >
                    <div className="gallery" id="product_parent">
                        {photos.map((img, index) => (
                            <div className="gallery-item" key={img.id || index}>
                                <div className="icons">
                                    <i
                                        onClick={() => deletePhoto(img.id)}
                                        className={`bi bi-trash ${isDeleting ? 'pending' : ''}`}
                                    ></i>
                                    <i
                                        className="bi bi-person-fill-add"
                                        id="add_linking"
                                        data-file-id={img.id}
                                        title="Add to face"
                                        onClick={() => setIsLinkingModal(img.id)}
                                    ></i>
                                    <i
                                        className="bi bi-download"
                                        onClick={() => downloadImage(img.photo_url, `photo-${img.id}.jpg`)}
                                    ></i>
                                </div>
                                <LazyImage src={img.photo_url} alt="Gallery Photo" onClick={() => setSelectedImage(img.photo_url)} />
                            </div>
                        ))}
                    </div>
                </InfiniteScroll>
            ) : (
                isFirstTimeLoadingPhoto ? (
                    <div className="text-center" style={{ margin: "20px 5px" }}>
                        <p style={{ fontSize: "18px" }}>Loading Photos</p>
                    </div>
                ) : (
                    <div className="text-center" style={{ margin: "20px 5px" }}>
                        <p style={{ fontSize: "18px" }}>No photos found</p>
                    </div>
                )

            )}

            {/* Fullscreen Preview */}
            {selectedImage && (
                <div className="overlay" onClick={() => setSelectedImage(null)}>
                    <button
                        className="back-button"
                        onClick={(e) => {
                            e.stopPropagation();
                            setSelectedImage(null);
                        }}
                    >
                        <i className="bi bi-arrow-left-circle"></i> Back
                    </button>
                    <img
                        src={selectedImage}
                        alt="Full Preview"
                        className="fullscreen-img"
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>
            )}

            {/* Face Linking Modal */}
            <Suspense fallback={<Loader />}>
                {isLinkingModal && <FaceLinking photo_id={isLinkingModal} onClose={() => setIsLinkingModal(null)} />}
            </Suspense>
        </main>
    );
};

export default FaceGallery;