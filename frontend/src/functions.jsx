import { config } from "./config";


// ----------------------------- Refresh Token --------------------------------

export const refreshToken = async () => {
    try {
        const access_token = localStorage.getItem('access_token', false);
        if (!access_token) {
            throw new Error('Please Login Again. Access token not found');
        }

        const response = await fetch(`${config.API_DOMAIN}/refresh-token`, {
            method: 'POST',
            credentials: 'include'
        });

        if (response.status === 401) { 
            console.warn('Refresh token expired. Logging out user...');
            localStorage.removeItem('access_token');
            return { success: false, error: 'Refresh token expired' };
        }

        if (!response.ok) {
            return { success: false, error: `Error ${response.status}: Refresh failed` };
        }

        const data = await response.json();
        if (data.access_token) {
            localStorage.setItem('access_token', data.access_token);
            return { success: true };
        }

        return { success: false, error: 'Invalid response from server' };
    } catch (error) {
        console.error("Token refresh failed:", error);
        throw error;
    }
};

// -------------------------- Is Authenticated Check ----------------------------

export const isAuthenticatedFun = async () => {
    try {
        const access_token = localStorage.getItem('access_token' || false);
        if (!access_token) return false;

        const response = await fetch(`${config.API_DOMAIN}/auth-status`, {
            credentials: 'include',
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${access_token}`
            }
        });

        if (response.status === 401) { 
            const refreshed = await refreshToken();
            if (refreshed.success) {
                return isAuthenticatedFun();
            }
            return false;
        }

        if (!response.ok) return false;

        const data = await response.json();
        return Boolean(data.authenticated);

    } catch (error) {
        console.error("Authentication check failed:", error);
        return false;
    }
};

// ------------------------------ Generic API Request -----------------------------
export const apiRequest = async ({
    API = null,
    DATA = {},
    METHOD = 'POST',
    ACCESS_TOKEN_REQUIRED = true,
    FORM_DATA = false
}) => {
    try {
        // Validate API endpoint
        if (!API) {
            throw new Error('API Endpoint not provided.');
        }

        // Get access token if required
        let ACCESS_TOKEN = null;
        if (ACCESS_TOKEN_REQUIRED) {
            ACCESS_TOKEN = localStorage.getItem('access_token');
            if (!ACCESS_TOKEN) {
                throw new Error('Access token not found. Please login.');
            }
        }

        // Prepare headers
        const headers = {};

        if (ACCESS_TOKEN) {
            headers['Authorization'] = `Bearer ${ACCESS_TOKEN}`;
        }

        if (!FORM_DATA) {
            headers['Content-Type'] = 'application/json';
        }

        // Prepare request options
        const options = {
            method: METHOD,
            headers,
            credentials: 'include'
        };

        // Handle request body
        if (METHOD !== 'GET') {
            if (FORM_DATA) {
                options.body = DATA; // Use FormData directly
            } else {
                // Ensure DATA is an object before stringifying
                if (DATA && typeof DATA === 'object' && !Array.isArray(DATA)) {
                    options.body = JSON.stringify(DATA);
                } else {
                    throw new Error('Invalid DATA format. Expected an object.');
                }
            }
        } else if (DATA && Object.keys(DATA).length > 0) {
            // Append query parameters to the URL for GET requests
            const queryParams = new URLSearchParams(DATA).toString();
            API = `${API}?${queryParams}`;
        }

        // Make the API request
        let response = await fetch(`${config.API_DOMAIN}${API}`, options);

        // Handle token refresh if unauthorized
        if (response.status === 401 && ACCESS_TOKEN_REQUIRED) {
            const refreshed = await refreshToken();
            if (refreshed.success) {
                // Update the access token in headers
                options.headers['Authorization'] = `Bearer ${localStorage.getItem('access_token')}`;
                // Retry the request
                response = await fetch(`${config.API_DOMAIN}${API}`, options);
            } else {
                throw new Error('Unauthorized: Token refresh failed. Please login again.');
            }
        }

        // Parse the response
        let data;
        try {
            data = await response.json();
        } catch (jsonError) {
            throw new Error('Invalid JSON response from API');
        }

        // Check if the response is successful
        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${data?.message || 'Request failed.'}`);
        }

        return data;

    } catch (error) {
        console.error('API Request Error:', error.message);
        throw error; 
    }
};

        