import { create } from 'zustand';

export interface User {
    id: string;
    name: string;
    email: string;
    role: string;
    isDefault?: boolean;
    status?: string;
    lastActive?: string;
}

export interface Role {
    id: number;
    name: string;
    description: string;
}

export interface Exception {
    id?: number | string;
    date: string;
    name: string;
    type: string;
    startTime?: string;
    endTime?: string;
}

interface SettingsState {
    // Modals
    isAddExceptionModalOpen: boolean;
    setIsAddExceptionModalOpen: (val: boolean) => void;
    isInviteModalOpen: boolean;
    setIsInviteModalOpen: (val: boolean) => void;
    isProfileModalOpen: boolean;
    setIsProfileModalOpen: (val: boolean) => void;

    // Notifications
    emailAlerts: boolean;
    setEmailAlerts: (val: boolean) => void;
    smsAlerts: boolean;
    setSmsAlerts: (val: boolean) => void;
    pushAlerts: boolean;
    setPushAlerts: (val: boolean) => void;

    // System
    maintenanceMode: boolean;
    setMaintenanceMode: (val: boolean) => void;

    // Appearance
    themeColor: string;
    setThemeColor: (val: string) => void;

    // Schedule
    workStart: string;
    setWorkStart: (val: string) => void;
    workEnd: string;
    setWorkEnd: (val: string) => void;
    newException: Exception;
    setNewException: (val: Exception) => void;
    exceptionsList: Exception[];
    setExceptionsList: (val: Exception[]) => void;

    // Users
    usersList: User[];
    setUsersList: (val: User[]) => void;
    newUser: { name: string; email: string; role: string };
    setNewUser: (val: { name: string; email: string; role: string }) => void;
    rolesList: Role[];
    setRolesList: (val: Role[]) => void;
    newRoleName: string;
    setNewRoleName: (val: string) => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
    // Modals
    isAddExceptionModalOpen: false,
    setIsAddExceptionModalOpen: (val) => set({ isAddExceptionModalOpen: val }),
    isInviteModalOpen: false,
    setIsInviteModalOpen: (val) => set({ isInviteModalOpen: val }),
    isProfileModalOpen: false,
    setIsProfileModalOpen: (val) => set({ isProfileModalOpen: val }),

    // Notifications
    emailAlerts: true,
    setEmailAlerts: (val) => set({ emailAlerts: val }),
    smsAlerts: false,
    setSmsAlerts: (val) => set({ smsAlerts: val }),
    pushAlerts: true,
    setPushAlerts: (val) => set({ pushAlerts: val }),

    // System
    maintenanceMode: false,
    setMaintenanceMode: (val) => set({ maintenanceMode: val }),

    // Appearance
    themeColor: "emerald",
    setThemeColor: (val) => set({ themeColor: val }),

    // Schedule
    workStart: "08:00",
    setWorkStart: (val) => set({ workStart: val }),
    workEnd: "19:00",
    setWorkEnd: (val) => set({ workEnd: val }),
    newException: { date: "", name: "", type: "closed", startTime: "08:00", endTime: "19:00" },
    setNewException: (val) => set({ newException: val }),
    exceptionsList: [
        { id: 1, date: "2026-05-01", name: "Fête du Travail", type: "closed" },
        { id: 2, date: "2026-12-24", name: "Ouverture exceptionnelle (Noël)", type: "open", startTime: "09:00", endTime: "17:00" },
    ],
    setExceptionsList: (val) => set({ exceptionsList: val }),

    // Users
    usersList: [],
    setUsersList: (val) => set({ usersList: val }),
    newUser: { name: "", email: "", role: "CLIENT" },
    setNewUser: (val) => set({ newUser: val }),
    rolesList: [
        { id: 1, name: "Super Administrateur", description: "Accès Total (Système, B2B, Réseau)" },
        { id: 2, name: "Admin Fonctionnel", description: "Gestion Locative & Clients B2B" },
    ],
    setRolesList: (val) => set({ rolesList: val }),
    newRoleName: "",
    setNewRoleName: (val) => set({ newRoleName: val }),
}));
