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

  // PATCH /me/ (see usuarios/views.py::MeView.patch, added 08/08) — same
  // shape as login()/register() above: the raw call lives here, not in a
  // separate src/api/ module, since every other account-identity endpoint
  // (token/registro/logout) is already called directly through `api` inside
  // this context rather than through a dedicated module — `user` state also
  // only exists here, so updating it right after a successful save (instead
  // of a separate GET /me/ round trip) keeps the rest of the app in sync
  // for free, same as login() already does.
  async function atualizarPerfil(dados) {
    try {
      const response = await api.patch("/me/", dados);
      setUser(response.data);
      return { success: true };
    } catch (error) {
      const data = error.response?.data || {
        detail: "Não foi possível atualizar seus dados.",
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
    atualizarPerfil,
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
