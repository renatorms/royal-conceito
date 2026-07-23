import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { CartProvider } from "@/contexts/CartContext";
import { PrivateRoute } from "@/components/PrivateRoute";
import { Header } from "@/components/Header";
import Login from "@/pages/Login";
import Registro from "@/pages/Registro";
import Catalogo from "@/pages/Catalogo";
import ProdutoDetalhe from "@/pages/ProdutoDetalhe";
import Carrinho from "@/pages/Carrinho";
import Checkout from "@/pages/Checkout";

function MeusPedidos() {
  return <h1 className="p-4">Meus Pedidos (placeholder, rota protegida)</h1>;
}

function PedidoConfirmado() {
  const location = useLocation();
  const pedidoId = location.state?.pedidoId;

  return (
    <div className="mx-auto max-w-lg px-4 py-16 text-center">
      <h1 className="text-2xl font-semibold">Pedido confirmado!</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        {pedidoId
          ? `Pedido #${pedidoId} recebido com sucesso.`
          : "Seu pedido foi recebido com sucesso."}
      </p>
      <Link
        to="/"
        className="mt-6 inline-block text-sm text-primary underline-offset-4 hover:underline"
      >
        Voltar ao catálogo
      </Link>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <BrowserRouter>
          <Header />
          <Routes>
            <Route path="/" element={<Catalogo />} />
            <Route path="/produtos/:id" element={<ProdutoDetalhe />} />
            <Route path="/carrinho" element={<Carrinho />} />
            <Route path="/login" element={<Login />} />
            <Route path="/registro" element={<Registro />} />
            <Route element={<PrivateRoute />}>
              <Route path="/checkout" element={<Checkout />} />
              <Route path="/pedido-confirmado" element={<PedidoConfirmado />} />
              <Route path="/meus-pedidos" element={<MeusPedidos />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </CartProvider>
    </AuthProvider>
  );
}

export default App;
