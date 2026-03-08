import { useCallback, useEffect } from "react";
import { useTenant } from "@/lib/TenantContext";
import { useSettingsStore } from "./useSettingsStore";

export function useSettingsState(activeTab: string) {
    const { currentTenant, authFetch } = useTenant();
    const isAdmin = currentTenant?.role === "SUPER_ADMIN";
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001";

    // Re-export state and setters from Zustand store
    const store = useSettingsStore();

    const fetchUsers = useCallback(async () => {
        try {
            const res = await authFetch(`${API_URL}/api/users`);
            if (res.ok) {
                store.setUsersList(await res.json());
            } else {
                console.error("Erreur serveur:", await res.text());
            }
        } catch (e) {
            console.error(e);
        }
    }, [API_URL, authFetch, store]);

    const fetchCustomRoles = useCallback(async () => {
        try {
            const res = await authFetch(`${API_URL}/api/custom-roles`);
            if (res.ok) {
                const customRolesDb = await res.json();

                // Keep default static roles + overwrite others
                const defaults = [
                    { id: 1, name: "Super Administrateur", description: "Accès Total (Système, B2B, Réseau)" },
                    { id: 2, name: "Admin Fonctionnel", description: "Gestion Locative & Clients B2B" }
                ];

                store.setRolesList([...defaults, ...customRolesDb]);
            }
        } catch (e) {
            console.error(e);
        }
    }, [API_URL, authFetch, store]);

    useEffect(() => {
        if (activeTab === "users") {
            fetchUsers();
            fetchCustomRoles();
        }
    }, [activeTab, fetchUsers, fetchCustomRoles]);

    const handleInviteUser = async (newUser: any, onSuccess: () => void, onError: (err: string) => void) => {
        try {
            const randomPassword = Math.random().toString(36).slice(-10) + "A1!";
            const res = await authFetch(`${API_URL}/api/users`, {
                method: "POST",
                body: JSON.stringify({ ...newUser, password: randomPassword })
            });
            if (res.ok) {
                onSuccess();
                await fetchUsers();
            } else {
                onError(`Erreur: ${await res.text()}`);
            }
        } catch (e) {
            console.error(e);
            onError(`Erreur réseau lors de l'invitation.`);
        }
    };

    const handleDeleteUser = async (id: string, name: string) => {
        if (!confirm(`Retirer l'accès à ${name} ?`)) return;
        try {
            const res = await authFetch(`${API_URL}/api/users/${id}`, { method: "DELETE" });
            if (res.ok) {
                await fetchUsers();
            } else {
                alert(`Erreur lors de la suppression: ${await res.text()}`);
            }
        } catch (e) {
            console.error(e);
            alert(`Erreur réseau lors de la suppression.`);
        }
    };

    const handleCreateRole = async (roleName: string, permissions: string[]) => {
        try {
            const res = await authFetch(`${API_URL}/api/custom-roles`, {
                method: "POST",
                body: JSON.stringify({ name: roleName, description: "Droits sur-mesure (Global)", permissions })
            });
            if (res.ok) {
                await fetchCustomRoles();
            } else {
                alert(`Erreur création profil: ${await res.text()}`);
            }
        } catch (err) {
            console.error("Erreur réseau (Role creation)", err);
        } finally {
            store.setIsProfileModalOpen(false);
            store.setNewRoleName("");
        }
    };

    const handleAddException = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const res = await authFetch(`${API_URL}/api/settings/exceptions`, {
                method: "POST",
                body: JSON.stringify(store.newException)
            });
            if (res.ok) {
                const saved = await res.json();
                store.setExceptionsList([...store.exceptionsList, saved]);
            } else {
                console.warn(`Fallback local: l'API a retourné ${res.status}`);
                const newId = Math.max(...store.exceptionsList.map(ex => Number(ex.id) || 0), 0) + 1;
                store.setExceptionsList([...store.exceptionsList, { ...store.newException, id: newId }]);
            }
        } catch (err) {
            console.error("Erreur réseau: Sauvegarde locale de l'exception", err);
            const newId = Math.max(...store.exceptionsList.map(ex => Number(ex.id) || 0), 0) + 1;
            store.setExceptionsList([...store.exceptionsList, { ...store.newException, id: newId }]);
        } finally {
            store.setIsAddExceptionModalOpen(false);
            store.setNewException({ date: "", name: "", type: "closed", startTime: "08:00", endTime: "19:00" });
        }
    };

    return {
        currentTenant, isAdmin,
        ...store,
        handleInviteUser, handleDeleteUser, handleAddException, handleCreateRole
    };
}
