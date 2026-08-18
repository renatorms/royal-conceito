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
import MeusFavoritos from "@/pages/MeusFavoritos";
import MinhaConta from "@/pages/MinhaConta";
import MinhaContaDados from "@/pages/MinhaContaDados";
import TrocasDevolucoes from "@/pages/TrocasDevolucoes";
import Sobre from "@/pages/Sobre";
import Privacidade from "@/pages/Privacidade";
import Contato from "@/pages/Contato";
import TermosDeUso from "@/pages/TermosDeUso";
import PoliticaTrocas from "@/pages/PoliticaTrocas";
import NotFound from "@/pages/NotFound";

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
            <Route path="/contato" element={<Contato />} />
            <Route path="/termos-de-uso" element={<TermosDeUso />} />
            <Route path="/politica-de-trocas" element={<PoliticaTrocas />} />
            <Route element={<PrivateRoute />}>
              <Route path="/checkout" element={<Checkout />} />
              <Route path="/pedido-confirmado" element={<PedidoConfirmado />} />
              <Route path="/meus-pedidos" element={<MeusPedidos />} />
              <Route path="/meus-pedidos/:id" element={<PedidoDetalhe />} />
              <Route path="/meus-enderecos" element={<MeusEnderecos />} />
              <Route path="/meus-favoritos" element={<MeusFavoritos />} />
              <Route path="/minha-conta" element={<MinhaConta />} />
              <Route path="/minha-conta/dados" element={<MinhaContaDados />} />
              <Route path="/trocas-e-devolucoes" element={<TrocasDevolucoes />} />
            </Route>
            <Route path="*" element={<NotFound />} />
          </Routes>
          <Footer />
        </BrowserRouter>
      </CartProvider>
    </AuthProvider>
  );
}

export default App;
