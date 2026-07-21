import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { PrivateRoute } from "@/components/PrivateRoute";

function Home() {
  return (
    <div>
      <h1>Royal Conceito</h1>
      <nav>
        <Link to="/login">Login</Link> | <Link to="/registro">Registro</Link> |{" "}
        <Link to="/meus-pedidos">Meus Pedidos</Link>
      </nav>
    </div>
  );
}

function Login() {
  return <h1>Login (placeholder)</h1>;
}

function Registro() {
  return <h1>Registro (placeholder)</h1>;
}

function MeusPedidos() {
  return <h1>Meus Pedidos (placeholder, rota protegida)</h1>;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
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
