import { createContext, useContext, useEffect, useState } from "react";
import api from "@/lib/axios";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api
      .get("/me/")
      .then((response) => setUser(response.data))
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false));
  }, []);

  async function login(username, password) {
    try {
      await api.post("/token/", { username, password });
      const response = await api.get("/me/");
      setUser(response.data);
      return { success: true };
    } catch (error) {
      const data = error.response?.data || {
        detail: "Usuário ou senha inválidos.",
      };
      return { success: false, error: data };
    }
  }

  async function register(dados) {
    try {
      await api.post("/registro/", dados);
      return { success: true };
    } catch (error) {
      const data = error.response?.data || {
        detail: "Não foi possível concluir o cadastro.",
      };
      return { success: false, error: data };
    }
  }

  async function logout() {
    try {
      await api.post("/logout/");
    } finally {
      setUser(null);
    }
  }

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    register,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth deve ser usado dentro de um AuthProvider");
  }
  return context;
}
