import React, { useState, useCallback, useEffect } from 'react';
import '../styles/UploadFile.css';
import { showToast } from "../utils/toast";
import { apiRequest } from "../functions";

const FileUploadComponent = ({isAuthenticated=false}) => {
    const [files, setFiles] = useState([]);
    const [maxPhotosReached, setMaxPhotosReached] = useState(false);
    const [isDataBaseFull, setIsDataBaseFull] = useState(false);

    useEffect(() => {
        document.title = 'Upload';
        if (isAuthenticated) {
            (async () => {
                try {
                    const response = await apiRequest({ API: '/upload', METHOD: 'GET' });
                    if (response.success && response.max_photos_reached) {
                        setIsDataBaseFull(response.max_photos_reached);
                        showToast('Database is full, Please contact us to increase the limit.', 'warning');
                    }
                } catch (error) {
                    showToast(error.message || 'An error occurred', 'error');
                }
            })();
        }
    }, [isAuthenticated]);

    

    const MAX_FILES = 50;

    const handleFileUpload = useCallback(async (file) => {
        if (isDataBaseFull) {
            showToast('Database is full, Please contact us to increase the limit.', 'warning');
            return;
        }
        if (files.length >= MAX_FILES) {
            showToast(`You can only upload up to ${MAX_FILES} files at once.`, 'warning');
            setMaxPhotosReached(true);
            return;
        }

        const isValid = await fileValidation(file);
        if (!isValid) return;
        if (checkFileExistence(file.name)) return;

        const fileId = generateElementId(file);
        if (fileId) {
            updateFileDetails(file, fileId);
            uploadFile(file, fileId);
        }
    }, [files, isDataBaseFull]);

    const fileValidation = async (file) => {
        if (!file) {
            showToast('No file provided for parsing.');
            return false;
        }
        const sizeInMB = file.size / (1024 * 1024);
        const maxSizeInMB = 20;

        if (sizeInMB > maxSizeInMB) {
            showToast(`Max size should be ${maxSizeInMB}MB.`);
            return false;
        }

        const allowedExtensions = ['jpg', 'jpeg', 'png', 'webp'];
        const fileExtension = file.name.split('.').pop().toLowerCase();

        if (!allowedExtensions.includes(fileExtension)) {
            showToast(`Only ${allowedExtensions.join(', ')} files are allowed.`);
            return false;
        }
        return true;
    };

    const checkFileExistence = (fileName) => {
        if (files.some(f => f.name === fileName)) {
            showToast('File already exists.');
            return true;
        }
        return false;
    };

    const generateElementId = (file) => {
        let validId = file.name.trim().replace(/[^a-zA-Z0-9_\u00C0-\uFFFF-]+/g, '-');
        if (/^\d/.test(validId)) {
            validId = `id-${validId}`;
        }
        validId = validId.replace(/-+/g, '-').replace(/-$/, '');
        return validId || Math.floor(Math.random() * 1000000);
    };

    const updateFileDetails = (file, fileId) => {
        const fileName = file.name;
        const extension = file.name.split('.').pop().toUpperCase();
        const fileSize = `${(file.size / (1024 * 1024)).toFixed(2)} MB`;
        setFiles(prevFiles => [...prevFiles, { id: fileId, name: fileName, extension, size: fileSize, status: 'Uploading...' }]);
    };

    const uploadFile = async (file, fileId) => {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await apiRequest({ API: '/upload', DATA: formData, METHOD: 'POST', FORM_DATA: true });

            if (response.success) {
                updateFileStatus(fileId, 'Uploaded', true);
            } else {
                updateFileStatus(fileId, 'Failed', true);
                showToast(data.message || 'File upload failed.');
            }

        } catch (error) {
            updateFileStatus(fileId, 'Failed', true);
            showToast(error.message || 'File upload failed due to a network error.');
        }
    };

    const updateFileStatus = (fileId, status, isSuccess) => {
        setFiles(prevFiles => prevFiles.map(f => f.id === fileId ? { ...f, status, isSuccess } : f));
    };

    const handleDrop = (e) => {
        e.preventDefault();
        if (files.length >= MAX_FILES) {
            showToast(`You can only upload up to ${MAX_FILES} files.`);
            return;
        }
        const droppedFiles = e.dataTransfer.files;
        if (droppedFiles) {
            Array.from(droppedFiles).forEach(file => handleFileUpload(file));
        }
    };

    const handleFileInputChange = (e) => {
        const selectedFiles = e.target.files;
        if (selectedFiles) {
            Array.from(selectedFiles).forEach(file => handleFileUpload(file));
        }
    };

    return (
        <div>
            <main className="container">
                <div className="accordion">
                    <div className="accordion-item active">
                        <div className="accordion-header">
                            <span className="title">Upload Photo</span>
                            <span className="icon"></span>
                        </div>
                        <div className="accordion-content">
                            {isDataBaseFull && (
                                <div className="warning_bar">
                                    You have reached your maximum photo limit. If you want to upload more photos, please contact us.
                                </div>
                            )}
                            <div
                                className={`upload-area ${isDataBaseFull ? 'disabled' : ''}`}
                                onDragOver={(e) => e.preventDefault()}
                                onDrop={handleDrop}
                            >
                                <label htmlFor="file">
                                    Drag file here or <span style={{ color: 'blue', fontWeight: '500' }}>browse</span>
                                </label>
                                <input
                                    type="file"
                                    id="file"
                                    name="file"
                                    accept="image/*"
                                    hidden
                                    multiple
                                    onChange={handleFileInputChange}
                                    disabled={maxPhotosReached || isDataBaseFull}
                                />
                            </div>
                            <div className="upload_status_container">
                                {files.map(file => (
                                    <div key={file.id} className="file-item">
                                        <div className="file-icon">{file.extension}</div>
                                        <div className="file-details">
                                            <div className="file-name">{file.name}</div>
                                            <div className="file-status">
                                                <span id="filesize">{file.size}</span>
                                                <span> • </span>
                                                <span className="file_status_txt">{file.status}</span>
                                            </div>
                                            <div className="progress-bar">
                                                <div className={`progress ${file.isSuccess ? 'success' : ''}`}></div>
                                            </div>
                                        </div>
                                        <button className="cancel-button"></button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </main>
            <div className="bottom_static">
                <span>Note: Uploading image will take some time to appear in the gallery</span>
            </div>
        </div>
    );
};

export default FileUploadComponent;