import React, { useEffect, useState, lazy, Suspense } from "react";
import '../styles/HomePage.css';
import '../styles/PhotoGallery.css';
import { apiRequest } from "../functions";
import { Link } from "react-router-dom";
import LazyImage from "../components/LazyImageLoader";
import InfiniteScroll from "react-infinite-scroll-component";
import LoadMoreFaceImg from "../assets/img/load_more.png";
import { showToast } from "../utils/toast";
import Loader from "../components/Loader";
const FaceLinking = lazy(() => import("../components/FaceLinking"));

const HomePageGallery = ({ isAuthenticated }) => {
    const [faces, setFaces] = useState([]);
    const [photos, setPhotos] = useState([]);
    const [facePage, setFacePage] = useState(1);
    const [photoPage, setPhotoPage] = useState(1);
    const [hasMoreFaces, setHasMoreFaces] = useState(true);
    const [hasMorePhotos, setHasMorePhotos] = useState(true);
    const [isLoadingFaces, setIsLoadingFaces] = useState(false);
    const [isLoadingPhotos, setIsLoadingPhotos] = useState(false);
    const [isFirstTimeLoadingPhoto, setIsFirstTimeLoadingPhoto] = useState(true);
    const [isDeleting, setIsDeleting] = useState(false);
    const [selectedImage, setSelectedImage] = useState(null);
    const [isLinkingModal, setIsLinkingModal] = useState(null);

    const DeletePhoto = async (photo_id) => {
        try {
            if (isDeleting) { showToast("Please wait...", "info"); return };
            setIsDeleting(true);
            const response = await apiRequest({ API: `/delete_photo`, DATA: { photo_id } });
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
    useEffect(() => {
        document.title = "WhatBM Photo - Home";
        (async () => {
            if (isAuthenticated) {
                fetchFaces(facePage);
                fetchPhotos(photoPage);
            }
        })();
    }, [isAuthenticated]);


    const fetchFaces = async (page) => {
        if (!hasMoreFaces || isLoadingFaces) return;
        try {
            setIsLoadingFaces(true);
            const response = await apiRequest({ API: `/faces?page=${page}`, METHOD: 'GET' });
            if (response.success) {
                setFaces(prev => [...prev, ...response.faces]);
                setFacePage(page + 1);
                setHasMoreFaces(response.has_next);
            }
        } catch (error) {
            console.error("Error fetching faces:", error);
        } finally {
            setIsLoadingFaces(false);
        }
    };

    const fetchPhotos = async (page) => {
        if (!hasMorePhotos || isLoadingPhotos) return;
        try {
            setIsLoadingPhotos(true);
            const response = await apiRequest({ API: `/photos?page=${page}`, METHOD: 'GET' });
            if (response.success) {
                setPhotos(prev => [...prev, ...response.photos]);
                setPhotoPage(page + 1);
                setHasMorePhotos(response.has_next);

                // Update only on the first fetch
                if (isFirstTimeLoadingPhoto) {
                    setIsFirstTimeLoadingPhoto(false);
                }
            }
        } catch (error) {
            console.error("Error fetching photos:", error);
        } finally {
            setIsLoadingPhotos(false);
        }
    };

    const downloadImage = (url, filename) => {
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = filename || "download.jpg";
        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);
    };

    return (
        <main className="container" id="gallery_main_container">
            {!isAuthenticated ? (
                <div className="text-center" style={{ margin: "20px 5px" }}>
                    <p style={{ fontSize: "18px" }}>You haven't Login yet</p>
                    <button className="custom_btn">
                        <Link to="/login" style={{ color: "white" }}>Login</Link>
                    </button>
                </div>
            ) : (
                <>
                    {/* Faces Section */}
                    {faces.length > 0 && (
                        <div className="categoriesss">
                            {faces.map(face => (
                                <div className="cats" key={face.id}>
                                    <Link to={`/face/${face.id}`}>
                                        <LazyImage src={face.face_url} alt={face.name || "Untitled"} />
                                    </Link>
                                    <Link to={`/face/${face.id}`}>
                                        <p>{face.name || "Untitled"}</p>
                                    </Link>
                                </div>
                            ))}
                            {hasMoreFaces && (
                                <div className="cats" id="load_more_face_parent">
                                    <a onClick={() => fetchFaces(facePage)}>
                                        <LazyImage src={LoadMoreFaceImg} alt="Load More" />
                                    </a>
                                    <p>{isLoadingFaces ? 'Loading...' : 'More..'}</p>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Gallery Section */}
                    {photos.length > 0 ? (
                        <InfiniteScroll
                            dataLength={photos.length}
                            next={() => fetchPhotos(photoPage)}
                            hasMore={hasMorePhotos}
                            loader={<button style={{ textAlign: 'center' }} className='show_more_btn' onClick={() => fetchPhotos(photoPage)} disabled={isLoadingPhotos}>{isLoadingPhotos ? 'Loading...' : 'Show More'}</button>}
                        >
                            <div className="gallery" id="product_parent">
                                {photos.map((img, index) => (
                                    <div className="gallery-item" key={img.id || index}>
                                        <div className="icons">
                                            <i onClick={() => DeletePhoto(img.id)} className={`bi bi-trash ${isDeleting ? 'pending' : ''}`}></i>
                                            <i className="bi bi-person-fill-add" id="add_linking" data-file-id={img.id} title="Add to face" onClick={() => setIsLinkingModal(img.id)}></i>
                                            <i className="bi bi-download" onClick={() => downloadImage(img.photo_url, `photo-${img.id}.jpg`)}></i>
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
                                <p style={{ fontSize: "18px" }}>You haven't uploaded any photos yet</p>
                                <button className="custom_btn">
                                    <Link to="/upload" style={{ color: "white" }}>Upload</Link>
                                </button>
                            </div>
                        )

                    )}

                    {/* Fullscreen Preview */}
                    {selectedImage && (
                        <div className="overlay" onClick={() => setSelectedImage(null)}>
                            <button className="back-button" onClick={(e) => {
                                e.stopPropagation();
                                setSelectedImage(null);
                            }}>
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

                    {/* Face linking component */}
                    <Suspense fallback={<Loader />}>
                        {isLinkingModal && <FaceLinking photo_id={isLinkingModal} onClose={() => setIsLinkingModal(null)} />}
                    </Suspense>
                </>
            )}
        </main>
    );
};

export default HomePageGallery;
