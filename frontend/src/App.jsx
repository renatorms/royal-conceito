import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { CartProvider } from "@/contexts/CartContext";
import { PrivateRoute } from "@/components/PrivateRoute";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import Login from "@/pages/Login";
import Registro from "@/pages/Registro";
import Catalogo from "@/pages/Catalogo";
import ProdutoDetalhe from "@/pages/ProdutoDetalhe";
import Carrinho from "@/pages/Carrinho";
import Checkout from "@/pages/Checkout";
import PedidoConfirmado from "@/pages/PedidoConfirmado";
import MeusPedidos from "@/pages/MeusPedidos";
import PedidoDetalhe from "@/pages/PedidoDetalhe";
import MeusEnderecos from "@/pages/MeusEnderecos";
import Perfil from "@/pages/Perfil";
import Sobre from "@/pages/Sobre";
import Privacidade from "@/pages/Privacidade";

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
            <Route path="/sobre" element={<Sobre />} />
            <Route path="/privacidade" element={<Privacidade />} />
            <Route element={<PrivateRoute />}>
              <Route path="/checkout" element={<Checkout />} />
              <Route path="/pedido-confirmado" element={<PedidoConfirmado />} />
              <Route path="/meus-pedidos" element={<MeusPedidos />} />
              <Route path="/meus-pedidos/:id" element={<PedidoDetalhe />} />
              <Route path="/meus-enderecos" element={<MeusEnderecos />} />
              <Route path="/perfil" element={<Perfil />} />
            </Route>
          </Routes>
          <Footer />
        </BrowserRouter>
      </CartProvider>
    </AuthProvider>
  );
}

export default App;
