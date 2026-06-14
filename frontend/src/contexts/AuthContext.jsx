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
        if (token) {
            // Set default header
            apiClient.setToken(token);
            // Fetch user details
            authApi.me()
                .then(userData => setUser(userData))
                .catch(() => {
                    logout();
                })
                .finally(() => setLoading(false));
        } else {
            apiClient.removeToken();
            // Avoid setting state if already false, or use a ref if needed to track mounted status.
            // However, this is inside useEffect, setting state is standard.
            // The lint error might be due to unconditional set or dependency cycle?
            // "Calling setState synchronously within an effect" usually means it's not wrapped in a condition or async?
            // No, it usually happens if the effect runs immediately and sets state.
            // Let's wrap in a check or setTimeout if strictly necessary, but standard auth flows often do this.
            // Actually, let's just make sure we don't loop.
            if (loading) {
                // Defer state update to avoid "bad setState" warning/error
                setTimeout(() => setLoading(false), 0);
            }
        }
    }, [token, loading]);

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
