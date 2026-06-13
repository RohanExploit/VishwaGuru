import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../api';
import { apiClient } from '../api/client';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem('token'));
    const [loading, setLoading] = useState(true);

    const logout = () => {
        setToken(null);
        setUser(null);
        apiClient.removeToken();
    };

    useEffect(() => {
        const handleLogout = () => logout();
        window.addEventListener('auth:logout', handleLogout);
        return () => window.removeEventListener('auth:logout', handleLogout);
    }, []);

    useEffect(() => {
        if (token) {
            // Set default header
            apiClient.setToken(token);

            // Only fetch user if not already set (prevents double fetch on login)
            if (!user) {
                authApi.me()
                    .then(userData => setUser(userData))
                    .catch(() => {
                        logout();
                    })
                    .finally(() => setLoading(false));
            } else {
                setLoading(false);
            }
        } else {
            apiClient.removeToken();
            setLoading(false);
        }
    }, [token]);

    const login = async (email, password) => {
        const data = await authApi.login(email, password);
        apiClient.setToken(data.access_token); // Eagerly set token
        setToken(data.access_token);

        if (data.user) {
            setUser(data.user);
            return data.user;
        }

        try {
            const userData = await authApi.me();
            setUser(userData);
            return userData;
        } catch (e) {
            return null;
        }
    };

    const signup = async (userData) => {
        return await authApi.signup(userData);
    };

    return (
        <AuthContext.Provider value={{ user, token, login, signup, logout, loading }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
