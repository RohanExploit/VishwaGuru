/**
 * 🪝 Supabase React Hooks
 * 
 * Custom React hooks for working with Supabase authentication and data
 */

import { useState, useEffect } from 'react';
import { supabase, getCurrentUser, onAuthStateChange } from './supabase';

/**
 * Hook to manage authentication state
 * @returns {{user: object|null, loading: boolean, error: Error|null}}
 */
export const useAuth = () => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        // Get initial session
        getCurrentUser()
            .then(({ data, error }) => {
                if (error) {
                    setError(error);
                } else {
                    setUser(data?.user || null);
                }
                setLoading(false);
            });

        // Listen for auth changes
        const unsubscribe = onAuthStateChange((event, session) => {
            setUser(session?.user || null);
            setLoading(false);
        });

        return () => unsubscribe();
    }, []);

    return { user, loading, error };
};

/**
 * Hook to fetch data from a Supabase table
 * @param {string} table - Name of the table
 * @param {object} options - Query options (select, filter, order, etc.)
 * @returns {{data: array|null, loading: boolean, error: Error|null, refetch: function}}
 */
export const useSupabaseQuery = (table, options = {}) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchData = async () => {
        try {
            setLoading(true);
            let query = supabase.from(table).select(options.select || '*');

            // Apply filters
            if (options.filter) {
                Object.entries(options.filter).forEach(([key, value]) => {
                    query = query.eq(key, value);
                });
            }

            // Apply ordering
            if (options.order) {
                query = query.order(options.order.column, {
                    ascending: options.order.ascending !== false
                });
            }

            // Apply limit
            if (options.limit) {
                query = query.limit(options.limit);
            }

            const { data: fetchedData, error: fetchError } = await query;

            if (fetchError) {
                setError(fetchError);
            } else {
                setData(fetchedData);
                setError(null);
            }
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [table, JSON.stringify(options)]);

    return { data, loading, error, refetch: fetchData };
};

/**
 * Hook to insert data into a Supabase table
 * @param {string} table - Name of the table
 * @returns {{insert: function, loading: boolean, error: Error|null}}
 */
export const useSupabaseInsert = (table) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const insert = async (data) => {
        try {
            setLoading(true);
            setError(null);

            const { data: insertedData, error: insertError } = await supabase
                .from(table)
                .insert(data)
                .select();

            if (insertError) {
                setError(insertError);
                return { data: null, error: insertError };
            }

            return { data: insertedData, error: null };
        } catch (err) {
            setError(err);
            return { data: null, error: err };
        } finally {
            setLoading(false);
        }
    };

    return { insert, loading, error };
};

/**
 * Hook to update data in a Supabase table
 * @param {string} table - Name of the table
 * @returns {{update: function, loading: boolean, error: Error|null}}
 */
export const useSupabaseUpdate = (table) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const update = async (id, data) => {
        try {
            setLoading(true);
            setError(null);

            const { data: updatedData, error: updateError } = await supabase
                .from(table)
                .update(data)
                .eq('id', id)
                .select();

            if (updateError) {
                setError(updateError);
                return { data: null, error: updateError };
            }

            return { data: updatedData, error: null };
        } catch (err) {
            setError(err);
            return { data: null, error: err };
        } finally {
            setLoading(false);
        }
    };

    return { update, loading, error };
};

/**
 * Hook to delete data from a Supabase table
 * @param {string} table - Name of the table
 * @returns {{deleteRecord: function, loading: boolean, error: Error|null}}
 */
export const useSupabaseDelete = (table) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const deleteRecord = async (id) => {
        try {
            setLoading(true);
            setError(null);

            const { error: deleteError } = await supabase
                .from(table)
                .delete()
                .eq('id', id);

            if (deleteError) {
                setError(deleteError);
                return { error: deleteError };
            }

            return { error: null };
        } catch (err) {
            setError(err);
            return { error: err };
        } finally {
            setLoading(false);
        }
    };

    return { deleteRecord, loading, error };
};

/**
 * Hook to subscribe to real-time changes in a Supabase table
 * @param {string} table - Name of the table
 * @param {function} callback - Function to call when data changes
 * @param {object} filter - Optional filter criteria
 */
export const useSupabaseSubscription = (table, callback, filter = {}) => {
    useEffect(() => {
        let subscription = supabase
            .channel(`${table}_changes`)
            .on(
                'postgres_changes',
                {
                    event: '*',
                    schema: 'public',
                    table: table,
                    filter: filter.filter || undefined
                },
                callback
            )
            .subscribe();

        return () => {
            subscription.unsubscribe();
        };
    }, [table, callback, JSON.stringify(filter)]);
};
