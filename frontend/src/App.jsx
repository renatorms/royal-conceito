import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { PrivateRoute } from "@/components/PrivateRoute";
import { Header } from "@/components/Header";
import Login from "@/pages/Login";
import Registro from "@/pages/Registro";
import Catalogo from "@/pages/Catalogo";
import ProdutoDetalhe from "@/pages/ProdutoDetalhe";

function MeusPedidos() {
  return <h1 className="p-4">Meus Pedidos (placeholder, rota protegida)</h1>;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Header />
        <Routes>
          <Route path="/" element={<Catalogo />} />
          <Route path="/produtos/:id" element={<ProdutoDetalhe />} />
          <Route path="/login" element={<Login />} />
          <Route path="/registro" element={<Registro />} />
          <Route element={<PrivateRoute />}>
            <Route path="/meus-pedidos" element={<MeusPedidos />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
