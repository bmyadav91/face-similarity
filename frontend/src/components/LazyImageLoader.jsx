import React, { useEffect, useState, useRef } from "react";
import LoaderImg from "../assets/img/loading.webp";

const LazyImage = ({ src, alt, onClick }) => {
    const imgRef = useRef(null);
    const [loaded, setLoaded] = useState(false);

    useEffect(() => {
        const observer = new IntersectionObserver((entries, observer) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    setLoaded(true);
                    observer.unobserve(entry.target);
                }
            });
        });

        if (imgRef.current) observer.observe(imgRef.current);

        return () => {
            if (imgRef.current) observer.unobserve(imgRef.current);
        };
    }, []);

    return (
        <img
            ref={imgRef}
            src={loaded ? src : LoaderImg}
            alt={alt || "Image"}
            className="lazy-image"
            onClick={onClick}
            style={{ cursor: "pointer" }} 
        />
    );
};

export default LazyImage;
